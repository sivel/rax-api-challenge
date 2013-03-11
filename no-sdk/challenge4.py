#!/usr/bin/env python

import raxcloudrest
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

    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()

    endpoint = rax.dns_svc_cat()

    headers, domains = rax.get('%s/domains/?name=%s' % (endpoint, domain))
    if not domains['domains']:
        print 'No matching domains: %s' % domain
        sys.exit(1)
    elif len(domains['domains']) > 1:
        print 'Multiple domains matched:'
        print '\n'.join([domain['name'] for domain in domains])
        sys.exit(1)

    domainid = domains['domains'][0]['id']
    headers, records = rax.get('%s/domains/%s/records' % (endpoint, domainid))
    namematches = filter(lambda x: x['name'] == args.fqdn, records['records'])
    exactmatches = filter(lambda x: x['name'] == args.fqdn and
                          x['data'] == args.ip, records['records'])

    if exactmatches:
        print 'Exact record match:'
        print '\n'.join(['%(name)s: %(data)s' %
                         record for record in exactmatches])
        print 'Not adding record'
        sys.exit(1)
    elif namematches:
        print 'Record already exists:'
        print '\n'.join(['%(name)s: %(data)s' %
                         record for record in namematches])
        print 'Adding additional record with same name'

    data = {
        'records': [
            {
                'ttl': 300,
                'name': args.fqdn,
                'type': 'A',
                'data': args.ip
            }
        ]
    }
    headers, record = rax.post('%s/domains/%s/records' % (endpoint, domainid),
                               data=data)
    print 'Record added'


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
