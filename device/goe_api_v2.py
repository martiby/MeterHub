#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

# 1.03.2022  Martin Steppuhn

import requests
import json
import time
import threading
import logging


class GoeApiV2:
    def __init__(self, ip_address, timeout=1, lifetime=10, log_name='goe'):
        """
        :param ip_address:  IP-Address
        :param timeout:     Timeout in seconds for request.
        :param lifetime:    Lifetime in seconds data ist valid
        """
        self.log = logging.getLogger(log_name)
        self.ip_address = ip_address
        self.timeout = timeout
        self.lifetime = lifetime
        self.data = None
        self.lifetime_timeout = time.perf_counter() + self.lifetime if self.lifetime else None  # set lifetime timeout
        self.log.debug("init address: {}".format(ip_address))

    def read(self):
        """
        Read information. Typically s, regularly also up to
        :return: None or Dictionary
        """
        t0 = time.perf_counter()
        url_template = "http://{}/api/status?filter=amp,frc,fsp,eto,nrg,car,wh"
        url = url_template.format(self.ip_address)
        d = None
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                r = json.loads(resp.content)
                # print(r)
                d = {}

                d['amp'] = r.get('amp', None)

                if r.get('fsp', None) == True:  # fsp = force single phase
                    d['phase'] = 1
                elif r.get('fsp', None) == False:  # fsp = force single phase
                    d['phase'] = 3
                else:
                    d['phase'] = None

                try:
                    d['p_set'] = d['amp'] * d['phase'] * 230
                except:
                    d['p_set'] = None

                try:
                    d['p'] = r['nrg'][11]
                except:
                    d['p'] = None

                d['stop'] = (r.get('frc', None) == 1)

                try:
                    d['e_cycle'] = round(r['wh'])
                except:
                    d['e_cycle'] = None

                d['eto'] = r.get('eto', None)

                car = r.get('car', None)
                if car == 1:
                    d['state'] = 'idle'
                elif car == 2:
                    d['state'] = 'charge'
                elif car == 3:
                    d['state'] = 'wait'
                elif car == 4:
                    d['state'] = 'complete'
                else:
                    d['state'] = 'error'

                self.lifetime_timeout = t0 + self.lifetime if self.lifetime else None  # set new lifetime timeout
                self.data = d
                self.log.debug("read done in {:.3f}s data: {}".format(time.perf_counter() - t0, d))
            else:
                raise ValueError("failed with status_code={}".format(resp.status_code))

        except Exception as e:
            self.log.debug("read failed {:.3f}s error: {}".format(time.perf_counter() - t0, e))
            if self.lifetime:
                if self.lifetime_timeout and time.perf_counter() > self.lifetime_timeout:
                    self.log.error("data lifetime expired")
                    self.lifetime_timeout = None  # disable timeout, restart with next valid receive
                    self.data = None  # clear data
            else:
                self.data = None  # without lifetime set self.data instantly to read result
        return d

    def get(self, key, default=None):
        """
        Get a single value

        :param key: string or tuple
        :param default: default
        :return: value or None
        """
        try:
            if isinstance(key, (tuple, list)):
                return self.data[key[0]][key[1]]
            else:
                return self.data[key]
        except:
            return default

    def set_amp(self, amp):
        self.log.debug("set_amp() amp={}".format(amp))
        try:
            r = requests.get('http://{}/api/set?amp={}'.format(self.ip_address, amp), timeout=1)
            if r.status_code == 200:
                data = json.loads(r.content)
                return True
            else:
                raise ValueError("failed with status_code={}".format(r.status_code))
        except Exception as e:
            self.log.error("set_amp() exception: {}".format(e))
            return False

    def stop(self):
        self.log.debug("stop()")
        try:
            r = requests.get('http://{}/api/set?frc=1&amp=6'.format(self.ip_address), timeout=1)
            if r.status_code == 200:
                data = json.loads(r.content)
                return True
            else:
                raise ValueError("failed with status_code={}".format(r.status_code))
        except Exception as e:
            self.log.error("force_off() exception: {}".format(e))
            return False

    def release(self):
        self.log.debug("release()")
        try:
            # r = requests.get('http://{}/api/set?frc=0&amp=6'.format(self.ip_address), timeout=1)
            r = requests.get('http://{}/api/set?frc=0'.format(self.ip_address), timeout=1)
            if r.status_code == 200:
                data = json.loads(r.content)
                return True
            else:
                raise ValueError("failed with status_code={}".format(r.status_code))
        except Exception as e:
            self.log.error("release_off() exception: {}".format(e))
            return False

    # def set_color(self, mode, rgb):
    #     """
    #     cid 	R/W 	string 	Config 	color_idle, format: #RRGGBB
    #     cwc 	R/W 	string 	Config 	color_waitcar, format: #RRGGBB
    #     cch 	R/W 	string 	Config 	color_charging, format: #RRGGBB
    #     cfi 	R/W 	string 	Config 	color_finished, format: #RRGGBB
    #
    #     http://192.168.0.25/api/set?cid=%22%2300FF00%22
    #
    #     :param rgb:
    #     :return:
    #     """
    #
    #     cmds = {"idle": "cid", "wait": "cwc", "charge":"cch", "complete": "cfi"}
    #
    #     self.log.debug("set_color()")
    #     try:
    #         r = requests.get('http://{}/api/set?cid=%22%23{}%22'.format(led, rgb), timeout=1)
    #         if r.status_code == 200:
    #             # data = json.loads(r.content)
    #             pass
    #         else:
    #             raise ValueError("failed with status_code={}".format(r.status_code))
    #     except Exception as e:
    #         self.log.error("set_color exception: {}".format(e))







if __name__ == "__main__":
    import time

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)-10s %(levelname)-6s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    logging.getLogger("goe").setLevel(logging.DEBUG)

    wallbox = GoeApiV2('192.168.0.25', timeout=5, lifetime=10)

    while True:
        wallbox.read()
        time.sleep(0.1)
        print(wallbox.data)
        time.sleep(2)

