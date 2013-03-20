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
import novaclient.exceptions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base server id to clone from')
    parser.add_argument('--dc', required=True, help='The region to '
                        'build the server in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)
    parser.add_argument('--name', required=False, help='The name of the new'
                        ' server. Defaults to adding "-clone" to the end of'
                        ' the original servers name')
    args = parser.parse_args()

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cs = pyrax.cloudservers

    try:
        base_details = cs.servers.get(args.base)
    except novaclient.exceptions.NotFound as e:
        raise SystemExit(e)

    newhost = (args.name if args.name else '%s-clone'
               % base_details.name)
    print ('Cloning %s to %s in %s' % (base_details.name, newhost,
           args.dc))

    base_image = base_details.create_image(base_details.name)

    while 1:
        print ('Sleeping 30 seconds before checking for image '
               'readiness...')
        time.sleep(30)
        image = cs.images.get(base_image)
        if image.status == 'ACTIVE':
            break

    print 'Building %s from image...' % newhost
    server = cs.servers.create(newhost, base_image, base_details.flavor['id'])

    statuses = ['ACTIVE', 'ERROR', 'UNKNOWN']
    while server.status not in statuses:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        server.get()
    print '%s online and ready...' % newhost
    print 'Cleaning up image...'
    cs.images.delete(base_image)
    t = prettytable.PrettyTable(['ID', 'Host', 'Status', 'IP',
                                 'Admin Password'])
    t.add_row([server.id, newhost, server.status,
               ', '.join(server.networks['public']), server.adminPass])
    print
    print t

if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
