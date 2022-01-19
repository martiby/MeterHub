#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

import os
import logging
import io
import time
from ftplib import FTP
from bottle import route, response


class Backup:
    def __init__(self):
        self.path = 'backup'  # default path
        self.data_minute_interval = 5  # minutes
        self.save_hour_interval = 6  # hours
        self.config = None  # list with keys saved from data
        self.ftp_config = None  # ftp configuration

        self.log = logging.getLogger('backup')
        self.hour = None  # hour 0..23
        self.minute = None  # minute 0..59

        self.csv_buffer = None  # string with full csv file content
        self.csv_date = None  # date string: "2022-01-17" suitable to csv

    def push(self, data):
        """

        """
        if not isinstance(self.config, (list, type)):  # abort without config
            return

        try:
            date = data['time'][0:10]  # 2000-12-31
            hour = int(data['time'][11:13])  # 0..23
            minute = int(data['time'][14:16])  # 0..59

            # Base interval (5min)
            if self.minute is not None and minute != self.minute and minute % self.data_minute_interval == 0:

                # try to restore buffer from file if buffer is empty
                if self.csv_buffer is None:
                    self.restore_from_file(date)

                # save buffer to file if date change (new day), clear buffer
                if self.csv_buffer and self.csv_date != date:
                    self.save()
                    self.csv_date, self.csv_buffer = None, None

                # save buffer to file if hour interval matches (e.g. every 6 hours)
                if self.csv_buffer and hour != self.hour and hour % self.save_hour_interval == 0:
                    self.save()

                # add header befor first bush
                if self.csv_buffer is None:
                    self.csv_buffer = ";".join(self.config) + '\n'  # csv header

                # append csv line
                self.csv_buffer += ";".join(["{}".format(data.get(k, '')) for k in self.config]) + '\n'  # append line
                self.csv_date = date

                self.log.debug("push {} {}".format(date, data))
            self.hour = hour
            self.minute = minute
        except Exception as e:
            self.log.error("push exception: {}".format(e))

    def save(self):
        self.save_to_file()
        if self.ftp_config:
            self.save_to_ftp()

    def save_to_file(self):
        """
        Save current CSV-Buffer to file
        """
        try:
            filename = self.csv_date + '.csv'  # filename  "2022-01-17.csv
            year = self.csv_date[0:4]  # year "2022"
            os.makedirs(os.path.join(self.path, year), exist_ok=True)
            open(os.path.join(self.path, year, filename), 'w').write(self.csv_buffer)
            self.log.info("file {} saved".format(filename))
        except Exception as e:
            self.log.error("save exception: {}".format(e))

    def save_to_ftp(self):
        try:
            t0 = time.perf_counter()
            filename = self.csv_date + '.csv'
            year = self.csv_date[0:4]

            ftp = FTP()
            # ftp.set_debuglevel(0)
            ftp.connect(self.ftp_config['server'], 21)
            ftp.login(self.ftp_config['user'], self.ftp_config['password'])
            ftp.cwd(self.ftp_config['path'])
            try:
                ftp.mkd(year)
            except:
                pass

            bio = io.BytesIO()
            bio.write(self.csv_buffer.encode())
            bio.seek(0)  # move to beginning of file

            ftp.cwd(year)
            ftp.storbinary('STOR {}'.format(filename), bio)  # send the file
            ftp.close()
            self.log.info("ftp upload {} done in {}s".format(filename, time.perf_counter() - t0))
        except Exception as e:
            self.log.error("ftp exception: {}".format(e))

    def restore_from_file(self, date):
        try:
            filename = date + '.csv'
            year = date[0:4]
            csv = open(os.path.join(self.path, year, filename), 'r').read()

            headline = csv.splitlines()[0].split(';')  # get headline from csv
            for i, k in enumerate(self.config):  # check if headline matches to config
                if headline[i] != k:
                    self.log.info("backup restore mismatch i={} file={} config={}".format(i, headline[i], k))
                    return
            self.csv_buffer = csv  # use restored file
            self.csv_date = date
            self.log.info("backup {} restored".format(filename))
        except IOError:
            pass
        except Exception as e:
            self.log.error("restore_from_file date={} exception={}".format(date, e))


backup = Backup()


@route("/backup")
def backup_csv():
    response.content_type = 'text/plain'
    return backup.csv_buffer()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-10s %(levelname)-6s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # ftp_config = {'server': '192.168.0.1', 'user': 'fritz.nas.pi', 'password': 'k98_Pi12-kl',
    #               'path': 'USB_STICK/METER_SERVER_BACKUP'}

    backup.path = "back_test"
    backup.config = ['time', 'timestamp', 'grid_imp_eto', 'grid_exp_eto', 'pv1_eto', 'pv2_eto', 'home_all_eto',
                     'flat_eto',
                     'bat_imp_eto', 'bat_exp_eto', 'car_eto', 'water_vto']

    backup.push({'time': '2021-05-20 12:05:00', 'home_all_eto': 1})
    backup.push({'time': '2021-05-20 12:10:00', 'home_all_eto': 2})
    backup.push({'time': '2021-05-20 18:20:00', 'home_all_eto': 3})
    backup.push({'time': '2021-05-21 00:00:00', 'home_all_eto': 4})
