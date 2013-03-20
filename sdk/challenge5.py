#!/usr/bin/env python

import pyrax
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
    instance = cdb.create(args.instance, flavor='m1.tiny', volume=1,
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
