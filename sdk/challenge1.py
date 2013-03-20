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
    parser.add_argument('base', help='The base hostname to use, 3x512MB')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)
    parser.add_argument('--image', required=False, help='The image ID to build'
                        ' the servers with',
                        default='5cebb13a-f783-4f8c-8058-c4182c724ccd')
    parser.add_argument('--count', required=False, help='Number of servers to '
                        'build. Default 3', default=3, type=int)

    args = parser.parse_args()

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cs = pyrax.cloudservers
    print 'Building servers in: %s' % args.dc
    servers = {}
    for i in xrange(0, abs(args.count)):
        host = '%s%d' % (args.base, i)
        print 'Creating server: %s' % host
        servers[host] = cs.servers.create(host, args.image, 2)
        print '%s: %s' % (host, servers[host].id)
    statuses = ['ACTIVE', 'ERROR', 'UNKNOWN']
    while filter(lambda server: server.status not in statuses,
                 servers.values()):
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        for host in servers:
            if servers[host].status in statuses:
                continue
            servers[host].get()

    t = prettytable.PrettyTable(['ID', 'Host', 'Status', 'IP',
                                 'Admin Password'])
    for host, server in servers.iteritems():
        t.add_row([server.id, host, server.status,
                   ', '.join(server.networks['public']), server.adminPass])
    print 'Servers online and ready...'
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
