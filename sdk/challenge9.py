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
import sys
import argparse
import time
import prettytable
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fqdn', help='The Fully Qualified Domain Name to use')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)
    parser.add_argument('--image', required=False, help='The image ID to build'
                        ' the servers with',
                        default='5cebb13a-f783-4f8c-8058-c4182c724ccd')
    parser.add_argument('--flavor', required=False, help='The flavor ID to'
                        ' build the servers with',
                        default=2, type=int)

    args = parser.parse_args()

    parts = args.fqdn.split('.')
    if len(parts) < 3:
        print 'Not a proper FQDN: %s' % args.fqdn
        sys.exit(1)
    domain = '.'.join(parts[-2:])

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cs = pyrax.cloudservers
    dns = pyrax.cloud_dns

    domains = dns.list()
    try:
        dom = filter(lambda x: x.name == domain, domains)[0]
    except IndexError:
        raise SystemExit('No matching domains: %s' % domain)

    print 'Building servers in: %s' % args.dc
    print 'Creating server: %s' % args.fqdn
    server = cs.servers.create(args.fqdn.split('.')[0], args.image,
                               args.flavor)
    adminPass = server.adminPass
    id = server.id
    print '%s: %s' % (args.fqdn, id)
    statuses = ['ACTIVE', 'ERROR', 'UNKNOWN']
    server = pyrax.utils.wait_until(server, 'status', statuses, interval=30,
                                    verbose=True)
    if server.status in ['ERROR', 'UNKNOWN']:
        server.get(id)
        raise SystemExit('Failed to build %s (%s, %s)' %
                         (id, server.status, server.progress))

    print 'Creating DNS record...'

    records = [
        {
            'ttl': 300,
            'name': args.fqdn,
            'type': 'A',
            'data': server.accessIPv4
        }
    ]
    domain = dom.add_records(records)
    print 'Record added'

    t = prettytable.PrettyTable(['ID', 'Host', 'Status', 'IP',
                                 'Admin Password'])
    t.add_row([server.id, args.fqdn, server.status,
               ', '.join(server.networks['public']), adminPass])
    print '\n\nServers online and ready...'
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
