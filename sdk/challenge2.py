#!/usr/bin/env python

import pyrax
import sys
import argparse
import time
import prettytable
import os
import novaclient.exceptions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base server id to clone from')
    parser.add_argument('--dc', required=True, help='The region to '
                        'build the server in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument('--name', required=False, help='The name of the new'
                        ' server. Defaults to adding "-clone" to the end of'
                        ' the original servers name')
    args = parser.parse_args()

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file)
    dc = args.dc if args.dc else 'DFW'
    cs = pyrax.connect_to_cloudservers(dc)

    try:
        base_details = cs.servers.get(args.base)
    except novaclient.exceptions.NotFound as e:
        raise SystemExit(e)

    newhost = (args.name if args.name else '%s-clone'
               % base_details.name)
    print ('Cloning %s to %s in %s' % (base_details.name, newhost,
           args.dc))

    base_image = base_details.create_image(base_details.name)

    while 1:
        print ('Sleeping 30 seconds before checking for image '
               'readiness...')
        time.sleep(30)
        image = cs.images.get(base_image)
        if image.status == 'ACTIVE':
            break

    print 'Building %s from image...' % newhost
    server = cs.servers.create(newhost, base_image, base_details.flavor['id'])

    adminPass = server.adminPass
    while 1:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        details = cs.servers.get(server.id)
        if details.status == 'ACTIVE':
            break
    print '%s online and ready...' % newhost
    print 'Cleaning up image...'
    cs.images.delete(base_image)
    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    t.add_row([details.id, newhost, details.accessIPv4, adminPass])
    print
    print t

if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
