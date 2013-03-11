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
    cs = pyrax.cloudservers
    dc = args.dc if args.dc else pyrax.default_region
    pyrax.connect_to_cloudservers(dc)
    print 'Building servers in: %s' % dc
    server_details = {}
    for i in xrange(0, 3):
        host = '%s%d' % (args.base, i)
        print 'Creating server: %s' % host
        server = cs.servers.create(host, args.image, 2)
        server_details[host] = {
            'id': server.id,
            'adminPass': server.adminPass,
            'ip': ''
        }
        print '%s: %s' % (host, server.id)
    complete = 0
    while complete < 3:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        for host, server in server_details.iteritems():
            details = cs.servers.get(server['id'])
            if details.status == 'ACTIVE':
                server_details[host]['ip'] = details.accessIPv4
                complete += 1
    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    for host, server in server_details.iteritems():
        t.add_row([server['id'], host, server['ip'], server['adminPass']])
    print 'Servers online and ready...'
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
