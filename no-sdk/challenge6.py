#!/usr/bin/env python

import raxcloudrest
import sys
import os
import requests
import argparse
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('container', help='The destination CloudFiles '
                        'container to enable CDN support on')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'])

    args = parser.parse_args()

    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    endpoints = rax.cf_svc_cat()
    cdn_endpoints = rax.cf_cdn_svc_cat()
    dc = args.dc if args.dc else endpoints.keys()[0]
    endpoint = endpoints.get(dc)
    cdn_endpoint = cdn_endpoints.get(dc)

    print 'Working in %s' % dc

    try:
        headers, files = rax.get('%s/%s' % (endpoint, args.container))
        print 'Container %s exists, using...' % args.container
    except requests.exceptions.HTTPError:
        print 'Container %s does not exist, creating...' % args.container
        headers, status = rax.put('%s/%s' % (endpoint, args.container))

    headers, status = rax.put('%s/%s' % (cdn_endpoint, args.container),
                              extra_headers={'X-CDN-Enabled': 'true'})

    print '%s CDN created and enabled:' % args.container
    print 'CDN URI: %s' % headers.get('X-Cdn-Uri')
    print 'CDN SSL URI: %s' % headers.get('X-Cdn-Ssl-Uri')
    print 'CDN Streaming URI: %s' % headers.get('X-Cdn-Streaming-Uri')

if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
