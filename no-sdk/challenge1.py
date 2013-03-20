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
import argparse
import time
import prettytable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base hostname to use, 3x512MB'
                        ' servers will be built using this base hostname')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument('--image', required=False, help='The image ID to build'
                        ' the servers with',
                        default='5cebb13a-f783-4f8c-8058-c4182c724ccd')

    args = parser.parse_args()
    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    endpoints = rax.next_gen_svc_cat()
    dc = args.dc if args.dc else endpoints.keys()[0]
    endpoint = endpoints.get(dc)
    print 'Building servers in: %s' % dc
    server_details = {}
    for i in xrange(0, 3):
        host = '%s%d' % (args.base, i)
        data = {
            'server': {
                'flavorRef': '2',
                'imageRef': args.image,
                'name': host,
            }
        }
        print 'Creating server: %s' % host
        headers, server = rax.post('%s/servers' % endpoint, data)
        server_details[host] = {
            'id': server['server']['id'],
            'adminPass': server['server']['adminPass'],
            'ip': ''
        }
        print '%s: %s' % (host, server['server']['id'])
    complete = 0
    while complete < 3:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        for host, server in server_details.iteritems():
            headers, details = rax.get('%s/servers/%s' %
                                       (endpoint, server['id']))
            if details['server']['status'] == 'ACTIVE':
                server_details[host]['ip'] = details['server']['accessIPv4']
                complete += 1
    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    for host, server in server_details.iteritems():
        t.add_row([server['id'], host, server['ip'], server['adminPass']])
    print 'Servers online and ready...'
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
