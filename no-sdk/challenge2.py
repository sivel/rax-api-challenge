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
import requests
import sys
import os
import argparse
import time
import prettytable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base server id to clone from')
    parser.add_argument('--dc', required=True, help='The region to '
                        'build the server in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument('--name', required=False, help='The name of the new'
                        ' server. Defaults to adding "-clone" to the end of'
                        ' the original servers name')
    args = parser.parse_args()
    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    endpoints = rax.next_gen_svc_cat()
    endpoint = endpoints.get(args.dc)
    try:
        headers, base_details = rax.get('%s/servers/%s' %
                                        (endpoint, args.base))
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)

    newhost = (args.name if args.name else '%s-clone'
               % base_details['server']['name'])
    print ('Cloning %s to %s in %s' % (base_details['server']['name'], newhost,
           args.dc))

    data = {
        'createImage': {
            'name': base_details['server']['name']
        }
    }
    headers, body = rax.post('%s/servers/%s/action' %
                             (endpoint, args.base), data)
    base_image = os.path.basename(headers.get('location'))
    while 1:
        print ('Sleeping 30 seconds before checking for image '
               'readiness...')
        time.sleep(30)
        headers, image = rax.get('%s/images/%s' % (endpoint, base_image))
        if image['image']['status'] == 'ACTIVE':
            break

    print 'Building %s from image...' % newhost
    data = {
        'server': {
            'flavorRef': base_details['server']['flavor']['id'],
            'imageRef': base_image,
            'name': newhost
        }
    }
    headers, server = rax.post('%s/servers' % endpoint, data)
    adminPass = server['server']['adminPass']
    while 1:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        headers, details = rax.get('%s/servers/%s' % (endpoint,
                                                      server['server']['id']))
        if details['server']['status'] == 'ACTIVE':
            break
    print '%s online and ready...' % newhost
    print 'Cleaning up image...'
    headers, status = rax.delete('%s/images/%s' % (endpoint, base_image))
    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    t.add_row([details['server']['id'], newhost,
               details['server']['accessIPv4'], adminPass])
    print
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
