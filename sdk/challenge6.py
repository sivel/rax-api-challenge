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
import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('container', help='The destination CloudFiles '
                        'container to enable CDN support on')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)

    args = parser.parse_args()

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cf = pyrax.cloudfiles

    print 'Working in %s' % args.dc

    try:
        container = cf.get_container(args.container)
        print 'Container %s exists, using...' % args.container
    except pyrax.exceptions.NoSuchContainer as e:
        print 'Container %s does not exist, creating...' % args.container
        container = cf.create_container(args.container)

    container.make_public(ttl=900)

    print '%s CDN created and enabled:' % args.container
    print 'CDN URI: %s' % container.cdn_uri
    print 'CDN SSL URI: %s' % container.cdn_ssl_uri
    print 'CDN Streaming URI: %s' % container.cdn_streaming_uri

if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
