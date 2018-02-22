"""
Copyright (c) 2016 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
The code, technical concepts, and all information contained herein, are the property of
Cisco Technology, Inc. and/or its affiliated entities, under various laws including copyright,
international treaties, patent, and/or contract. Any use of the material herein must be in
accordance with the terms of the License.
All rights not expressly granted by the License are reserved.

Unless required by applicable law or agreed to separately in writing, software distributed under
the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied.

Purpose:      Blackbox test for the Deployment manager

"""

import time
import argparse
import requests
import eventlet
from requests.exceptions import RequestException

from pnda_plugin import PndaPlugin
from pnda_plugin import Event

TIMESTAMP_MILLIS = lambda: int(round(time.time() * 1000))
TESTBOTPLUGIN = lambda: FLINK()


class Flink(PndaPlugin):
    '''
    Blackbox test plugin for the Deployment Manager
    '''

    def __init__(self):
        pass

    def read_args(self, args):
        '''
        This class argument parser.
        This shall come from main runner in the extra arg
        '''
        parser = argparse.ArgumentParser(prog=self.__class__.__name__, \
         usage='%(prog)s [options]', description='Key metrics from CDH cluster')
        parser.add_argument('--fhendpoint', default='http://localhost:8082', \
         help='Flink History Server endpoint e.g. http://localhost:8082')

        return parser.parse_args(args)


    @staticmethod
    def validate_api_response(response, path):
        expected_codes = [200, 404]

        if response.status_code in expected_codes:
            return 'SUCCESS', None
        else:
            return 'FAIL', path

    def runner(self, args, display=True):
        """
        Main section.
        """
        plugin_args = args.split() \
        if args is not None and args.strip() \
        else ""

        options = self.read_args(plugin_args)
        cause = []
        values = []

        history_server_available_ok = False
        history_server_available_ms = -1

        # noinspection PyBroadException
        try:
            path = '/joboverview'
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.get("%s%s" % (options.fhendpoint, path), timeout=20)
            end = TIMESTAMP_MILLIS()

            history_server_available_ms = end - start
            status, msg = Flink.validate_api_response(req, path)

            if status == 'SUCCESS':
                history_server_available_ok = True
            else:
                cause.append(msg)

        except RequestException:
            cause.append('Unable to connect to the Flink History Server (request path = {})'.format(path))

        except Exception as e:
            cause.append('Platform Testing Client Error- ' + str(e))

        values.append(Event(TIMESTAMP_MILLIS(), "flink",
                            "flink.history_server_available_ms", [], packages_available_ms))

        values.append(Event(TIMESTAMP_MILLIS(), "flink",
                            "flink.history_server_available_ok", [], packages_available_ok))

        health = "OK"
        if not history_server_available_ok:
            health = "ERROR"

        values.append(Event(TIMESTAMP_MILLIS(), 'flink',
                            'flink.health', cause, health))
        if display:
            self._do_display(values)
        return values
