#!/usr/bin/env python

import pyrax
import sys
import os
import requests
import argparse
import re


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

    if not re.match('^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                    '(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', str(args.ip)):
        print 'Not a proper IP: %s' % args.ip
        sys.exit(1)

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
