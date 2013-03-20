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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fqdn', help='Fully Qualified Domain Name')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'])
    args = parser.parse_args()

    parts = args.fqdn.split('.')
    if len(parts) < 3:
        print 'Not a proper FQDN: %s' % args.fqdn
        sys.exit(1)
    domain = '.'.join(parts[-2:])

    container = '-'.join(parts[:-2])

    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    cf_endpoints = rax.cf_svc_cat()
    cdn_endpoints = rax.cf_cdn_svc_cat()
    dns_endpoint = rax.dns_svc_cat()
    dc = args.dc if args.dc else cf_endpoints.keys()[0]
    cf_endpoint = cf_endpoints.get(dc)
    cdn_endpoint = cdn_endpoints.get(dc)

    print 'Working in %s' % dc

    try:
        headers, files = rax.get('%s/%s' % (cf_endpoint, container))
        print 'Container exists...'
    except requests.exceptions.HTTPError:
        print 'Container %s does not exist, creating...' % container
        headers, status = rax.put('%s/%s' % (cf_endpoint, container))

    headers, status = rax.put('%s/%s' % (cdn_endpoint, container),
                              extra_headers={'X-CDN-Enabled': 'true'})

    cdn_host = headers.get('X-Cdn-Uri').replace('http://', '')

    headers, status = rax.post('%s/%s/' % (cf_endpoint, container), data='',
                               extra_headers={'X-Container-Meta-Web-Index':
                                              'index.html'})

    headers, status = rax.put('%s/%s/index.html' %
                              (cf_endpoint, container), 'It Works!',
                              extra_headers={
                                  'Content-Type': 'text/html'})

    headers, domains = rax.get('%s/domains/?name=%s' % (dns_endpoint, domain))
    if not domains['domains']:
        print 'No matching domains: %s' % domain
        sys.exit(1)
    elif len(domains['domains']) > 1:
        print 'Multiple domains matched:'
        print '\n'.join([domain['name'] for domain in domains])
        sys.exit(1)

    domainid = domains['domains'][0]['id']

    data = {
        'records': [
            {
                'ttl': 300,
                'name': args.fqdn,
                'type': 'CNAME',
                'data': cdn_host
            }
        ]
    }
    headers, record = rax.post('%s/domains/%s/records' %
                               (dns_endpoint, domainid), data=data)


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
