#!/usr/bin/env python

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
    parser.add_argument('source', help='The source file or directory to '
                        'upload to CloudFiles')
    parser.add_argument('destination', help='The destination CloudFiles '
                        'container to upload files to. Will be created if it '
                        'does not exist')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'])

    args = parser.parse_args()

    source = os.path.abspath(os.path.normpath(args.source))
    destination = re.sub(r'\W+', '-', args.destination)
    if args.destination != destination:
        print ('The name of the destination container was sanitized: %s' %
               destination)

    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    endpoints = rax.cf_svc_cat()
    dc = args.dc if args.dc else endpoints.keys()[0]
    endpoint = endpoints.get(dc)

    print 'Uploading to %s in %s' % (destination, dc)

    try:
        headers, files = rax.get('%s/%s' % (endpoint, destination))
    except requests.exceptions.HTTPError:
        print 'Container %s does not exist, creating...' % destination
        headers, status = rax.put('%s/%s' % (endpoint, destination))

    if os.path.isfile(source):
        print 'Uploading %s...' % source
        content_type = mimetypes.guess_type(source)[0]
        with open(source) as f:
            headers, status = rax.put('%s/%s/%s' %
                                      (endpoint, destination,
                                       os.path.basename(source)), f,
                                      extra_headers={
                                          'Content-Type': content_type})
    elif os.path.isdir(source):
        files = os.listdir(source)
        if not files:
            print 'No files to upload'
            sys.exit(1)
        for sfile in files:
            filepath = os.path.join(source, sfile)
            if os.path.isfile(filepath):
                print 'Uploading %s...' % filepath
                content_type = mimetypes.guess_type(filepath)[0]
                with open(filepath) as f:
                    headers, status = rax.put('%s/%s/%s' %
                                              (endpoint, destination,
                                               os.path.basename(filepath)), f,
                                              extra_headers={
                                                  'Content-Type': content_type}
                                              )
            else:
                print 'Not uploading directory %s' % filepath


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
