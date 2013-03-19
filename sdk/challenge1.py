#!/usr/bin/env python

import pyrax
import sys
import argparse
import time
import prettytable
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base hostname to use, 3x512MB'
                        ' servers will be built using this base hostname')
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument('--image', required=False, help='The image ID to build'
                        ' the servers with',
                        default='5cebb13a-f783-4f8c-8058-c4182c724ccd')

    args = parser.parse_args()

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file)
    dc = args.dc if args.dc else pyrax.default_region
    cs = pyrax.connect_to_cloudservers(dc)
    print 'Building servers in: %s' % dc
    servers = {}
    for i in xrange(0, 3):
        host = '%s%d' % (args.base, i)
        print 'Creating server: %s' % host
        servers[host] = cs.servers.create(host, args.image, 2)
        print '%s: %s' % (host, servers[host].id)
    while filter(lambda server: server.status != 'ACTIVE', servers.values()):
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        for host in servers:
            if servers[host].status == 'ACTIVE':
                continue
            servers[host].get()

    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    for host, server in servers.iteritems():
        t.add_row([server.id, host, ', '.join(server.networks['public']),
                   server.adminPass])
    print 'Servers online and ready...'
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
