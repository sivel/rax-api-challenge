#!/usr/bin/env python

import pyrax
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
