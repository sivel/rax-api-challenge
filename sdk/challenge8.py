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
    parser.add_argument('fqdn', help='Fully Qualified Domain Name')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)
    args = parser.parse_args()

    parts = args.fqdn.split('.')
    if len(parts) < 3:
        print 'Not a proper FQDN: %s' % args.fqdn
        sys.exit(1)
    domain = '.'.join(parts[-2:])

    container = '-'.join(parts[:-2])

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cf = pyrax.cloudfiles
    dns = pyrax.cloud_dns

    print 'Working in %s' % args.dc

    try:
        cont = cf.get_container(container)
        print 'Container exists...'
    except pyrax.exceptions.NoSuchContainer:
        print 'Container %s does not exist, creating...' % container
        cont = cf.create_container(container)

    cont.make_public(ttl=900)

    cont.set_web_index_page('index.html')

    cont.store_object('index.html', 'It Works!', content_type='text/html')

    domains = dns.list()
    try:
        dom = filter(lambda x: x.name == domain, domains)[0]
    except IndexError:
        print 'No matching domains: %s' % domain
        print 'Site available at %s' % cont.cdn_uri
        sys.exit(1)

    records = [
        {
            'ttl': 300,
            'name': args.fqdn,
            'type': 'CNAME',
            'data': cont.cdn_uri.replace('http://', '')
        }
    ]
    domain = dom.add_records(records)
    print 'Record added: %s' % args.fqdn

if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
