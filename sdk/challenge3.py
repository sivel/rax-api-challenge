#!/usr/bin/env python

import pyrax
import sys
import os
import requests
import argparse
import time
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='The source file or directory to '
                        'upload to CloudFiles')
    parser.add_argument('destination', help='The destination CloudFiles '
                        'container to upload files to. Will be created if it '
                        'does not exist')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)

    args = parser.parse_args()

    source = os.path.abspath(os.path.normpath(args.source))
    destination = re.sub(r'\W+', '-', args.destination)
    if args.destination != destination:
        print ('The name of the destination container was sanitized: %s' %
               destination)

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cf = pyrax.cloudfiles

    print 'Uploading to %s in %s' % (destination, args.dc)

    try:
        files = cf.get_container(destination)
    except pyrax.exceptions.NoSuchContainer as e:
        print 'Container %s does not exist, creating...' % destination
        cf.create_container(destination)

    if os.path.isfile(source):
        print 'Uploading %s...' % source
        cf.upload_file(destination, source)
    elif os.path.isdir(source):
        print 'Uploading contents of %s...' % source
        upload_key = cf.upload_folder(source, container=destination)
        try:
            while pyrax.cloudfiles.get_uploaded(upload_key):
                pass
        except TypeError:
            pass


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
