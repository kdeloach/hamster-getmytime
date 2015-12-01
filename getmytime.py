#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import argparse
import json
import requests
import sys
import time


class GetMyTimeApi(object):
    URL = 'https://app.getmytime.com/service.aspx'

    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def login(self, username, password):
        params = {
            'object': 'getmytime.api.usermanager',
            'method': 'login',
        }
        form_data = {
            'username': username,
            'password': password,
        }

        r = requests.post(self.URL, params=params, data=form_data)

        if 'Incorrect' in r.text:
            raise Exception(r.text)

        self.cookies = r.cookies

        time.sleep(1)

    def fetch_lookups(self):
        if hasattr(self, 'customers'):
            return

        params = {
            'object': 'getmytime.api.managemanager',
            'method': 'fetchLookups'
        }
        form_data = {
            'lookups': '[customerjobs],[serviceitems]'
        }

        r = requests.post(self.URL, params=params, data=form_data,
                          cookies=self.cookies)
        data = r.json()
        customers = dict((row['strClientJobName']
                          .lower()
                          .replace('&amp;', '&'),
                          row['intClientJobListID'])
                         for row in data['customerjobs']['rows'])

        tasks = dict((row['strTaskName'].lower(), row['intTaskListID'])
                     for row in data['serviceitems']['rows'])

        self.customers = customers
        self.tasks = tasks

        time.sleep(1)

    def create_time_entry(self, activity, customer, comments, start_time,
                          end_time, tags, minutes):
        self.fetch_lookups()

        tags = tags if tags else []

        employeeid = self.cookies['userid']
        customerid = self.customers[customer.lower()]
        billable = 'billable' in tags

        if activity in self.tasks:
            taskid = self.tasks[activity.lower()]
        else:
            taskid = self.tasks['Software Development'.lower()]

        params = {
            'object': 'getmytime.api.timeentrymanager',
            'method': 'createTimeEntry',
        }
        form_data = {
            'employeeid': employeeid,
            'startdate': start_time,
            'startdatetime': start_time,
            'minutes': int(minutes),
            'customerid': customerid,
            'taskid': taskid,
            'comments': comments,
            'billable': billable,
            'projectid': 139,  # Basic
            'classid': 0,
            'starttimer': 'false',
        }

        print('Submitting {} - {}, {}'.format(start_time, end_time, customer))

        if self.dry_run:
            print(form_data)
        else:
            r = requests.post(self.URL, params=params, data=form_data,
                              cookies=self.cookies)

            if 'error' in r.text:
                raise Exception(r.text)

            print(r.status_code, r.text)

            time.sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('password')
    parser.add_argument('--dry-run', action='store_const', const=True,
                        default=False)
    parser.add_argument('--from-json', action='store_const', const=True,
                        default=False, help='Read JSON data from stdin')
    args = parser.parse_args()

    if args.from_json:
        entries = json.loads(sys.stdin.read())
        api = GetMyTimeApi(dry_run=args.dry_run)
        api.login(args.username, args.password)
        for entry in entries:
            api.create_time_entry(**entry)
        print('Done')
    else:
        print('Nothing to do')


if __name__ == '__main__':
    main()
