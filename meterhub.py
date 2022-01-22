#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

# 23.01.2022    Martin Steppuhn     MeterHub project bundle

"""
    MeterHub

    Combine all data sources (electricity meter, inverter, wallbox, etc.) and make them available via an HTTP API.

    Example: http://192.168.0.10:8008  --> JSON

    {
     "time": "2021-10-21 09:24:54",
     "measure_time": 0.405,
     "pv1_eto": 15240930,
     "pv2_eto": 7399770,
     "pv1_p": 2688,
     "grid_p": -2284,
     "car_p": 0
     }
"""

import logging
import threading
import time
from datetime import datetime
from bottle import route, run
from backup import backup
from eastron import SDM  # Powermeter with Modbus
from fronius import Symo  # PV Inverter
from goe import Goe  # GO-E Wallbox
from json_request import JsonRequest  # HTTP API for Battery system
# Devices
from sml import Sml  # IP Coupler interface to grid power meter
from trace import trace
import config

__name__ = "MeterHub"
__version__ = "0.9.1"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-10s %(levelname)-6s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

data = {}  # actual dataset


# === Hooks for Webserver ===

@route("/")
def index():
    return data

@route("/version")
def version():
    return __name__ + ' V' + __version__



# start bottle/waitress webserver thread
threading.Thread(target=run, kwargs=dict(host='0.0.0.0', port=8008, server='waitress'), daemon=True).start()

# init devices
sml_port = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0"  # IR Coupler
sdm_port = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.2:1.0-port0"  # USB-RS485

sml = Sml(port=sml_port, lifetime=10, log_name='mt175')
sdm630 = SDM(sdm_port, type="SDM630", address=1, lifetime=10, log_name='sdm630')
sdm72 = SDM(sdm_port, type="SDM72", address=3, lifetime=10, log_name='sdm72')
pv = Symo('192.168.0.20', log_name='fronius')
goe = Goe('192.168.0.25', log_name='goe')
bat = JsonRequest('http://192.168.0.10:8888/api/data', lifetime=10, log_name='bat')  # PyBattery
water = JsonRequest('http://192.168.0.24/json', lifetime=10 * 60 + 10, log_name='water')  # Water-Meter

pv.start_tread(thread_sleep=0.5)  # read fronius in extra thread

backup.ftp_config = config.ftp_config
backup.save_hour_interval = 6
backup.config = ['time', 'timestamp', 'grid_imp_eto', 'grid_exp_eto', 'pv1_eto', 'pv2_eto', 'home_all_eto', 'flat_eto',
                 'bat_imp_eto', 'bat_exp_eto', 'car_eto', 'water_vto']

t_minute = 0

# main loop

while True:
    t0 = time.perf_counter()  # store start time
    sdm630.read(['p', 'e_total'])  # home  (legacy e_total, import is better)
    sdm72.read(['p', 'e_total'])  # flat  (legacy e_total, import is better)
    sml.read()  # read IR coupler
    goe.read()  # read Wallbox
    bat.read()  # read Battery

    if t0 > t_minute:  # water read only once a minute
        t_minute = t0 + 60
        water.read()

    # assemble data
    data = {
        'measure_time': round(time.perf_counter() - t0, 3),
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'timestamp': int(datetime.utcnow().timestamp()),

        # Grid meter
        'grid_imp_eto': sml.get('e_import'),  # MT175
        'grid_exp_eto': sml.get('e_export'),  # MT175
        'grid_p': sml.get('p'),

        # PV
        'pv1_eto': pv.get(('e_total', 0)),  # Fronius Symo 7 (Süden)
        'pv2_eto': pv.get(('e_total', 1)),  # Fronius Symo 6 (Norden)
        'pv1_p': pv.get(('p', 0)),
        'pv2_p': pv.get(('p', 1)),
        'pv_p': pv.get(('p', 0), default=0) + pv.get(('p', 1), default=0),

        # Home
        'home_all_eto': sdm630.get('e_total'),  # SDM630, Haus Gesamtverbrauch
        'home_all_p': sdm630.get('p'),

        # Flat
        'flat_eto': sdm72.get('e_total'),  # SDM72, Einliegerwohnung
        'flat_p': sdm72.get('p'),

        # Battery
        'bat_imp_eto': bat.get('bat_e_imp'),  # HomeBattery, Ladung / SDM120
        'bat_exp_eto': bat.get('bat_e_exp'),  # HomeBattery, Einspeisung / SDM120
        'bat_soc': bat.get('bat_soc'),  # HomeBattery, SOC
        'bat_p': bat.get('bat_p'),

        # Wallbox
        'car_eto': goe.get('eto'),
        'car_p': goe.get('p'),
        'car_p_set': goe.get('p_set'),
        'car_e_cycle': goe.get('e_cycle'),
        'car_amp': goe.get('amp'),
        'car_phase': goe.get('phase'),
        'car_force_stop': goe.get('stop'),
        'car_state': goe.get('state'),

        # Water
        'water_vto': water.get(('main', 'value'))
    }

    trace.push(data)  # save dataset to trace module
    backup.push(data)  # save 5min Dataset to local Backup (additional to FTP)

    while int(t0) == int(time.perf_counter()):  # update not faster than once a second
        time.sleep(0.1)
