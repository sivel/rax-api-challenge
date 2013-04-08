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

import pyrax
import os
import argparse
import random
import prettytable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('instance', help='Name of database instance')
    parser.add_argument('database', help='name of database')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the database in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)
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

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cdb = pyrax.cloud_databases

    print 'Creating DB instance in %s' % args.dc

    users = [
        {
            'databases': [
                {
                    'name': args.database
                }
            ],
            'name': user,
            'password': password
        }
    ]
    instance = cdb.create(args.instance, flavor='1GB Instance', volume=1,
                          users=users, databases=[{'name': args.database}])

    t = prettytable.PrettyTable(['ID', 'Name', 'Hostname', 'Database', 'User',
                                 'Password'])
    t.add_row([instance.id, instance.name,
               instance.hostname, args.database, user,
               password])
    print
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
