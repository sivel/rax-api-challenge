#!/usr/bin/env python

import pyrax
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
