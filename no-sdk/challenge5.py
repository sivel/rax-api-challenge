#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Matt Martz
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import raxcloudrest
import sys
import os
import requests
import argparse
import time
import re
import mimetypes
import random
import string
import prettytable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('instance', help='Name of database instance')
    parser.add_argument('database', help='name of database')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the database in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument('--user', required=False, help='The user to create for'
                        'database access. Defaults to current user')
    parser.add_argument('--password', required=False,
                        help='Password for DB user')

    args = parser.parse_args()

    if not args.password:
        chars = string.ascii_letters + string.digits
        random.seed = os.urandom(1024)
        password = ''.join(random.choice(chars) for i in xrange(12))
    else:
        password = args.password

    if not args.user:
        user = os.getlogin()
    else:
        user = args.user

    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    endpoints = rax.db_svc_cat()
    dc = args.dc if args.dc else endpoints.keys()[0]
    endpoint = endpoints.get(dc)

    print 'Creating DB instance in %s' % dc

    data = {
        'instance': {
            'databases': [
                {
                    'name': args.database
                }
            ],
            'users': [
                {
                    'databases': [
                        {
                            'name': args.database
                        }
                    ],
                    'name': user,
                    'password': password
                }
            ],
            'flavorRef': '%s/flavors/1',
            'name': args.instance,
            'volume': {
                'size': 1
            }
        }
    }

    headers, instance = rax.post('%s/instances' % endpoint, data)

    t = prettytable.PrettyTable(['ID', 'Name', 'Hostname', 'Database', 'User',
                                 'Password'])
    t.add_row([instance['instance']['id'], instance['instance']['name'],
               instance['instance']['hostname'], args.database, user,
               password])

    print
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
