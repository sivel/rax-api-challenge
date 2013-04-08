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
import socket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fqdn', help='Fully Qualified Domain Name')
    parser.add_argument('ip', help='IP Address')

    args = parser.parse_args()

    parts = args.fqdn.split('.')
    if len(parts) < 3:
        print 'Not a proper FQDN: %s' % args.fqdn
        sys.exit(1)
    domain = '.'.join(parts[-2:])

    try:
        socket.inet_aton(args.ip)
    except:
        raise SystemExit('Not a proper IPv4 address: %s' % args.ip)

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file)
    dns = pyrax.cloud_dns

    domains = dns.list()
    try:
        dom = filter(lambda x: x.name == domain, domains)[0]
    except IndexError:
        print 'No matching domains: %s' % domain
        sys.exit(1)

    records = [
        {
            'ttl': 300,
            'name': args.fqdn,
            'type': 'A',
            'data': args.ip
        }
    ]
    domain = dom.add_records(records)
    print 'Record added'


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
