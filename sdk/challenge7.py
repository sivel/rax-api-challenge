#!/usr/bin/env python

import pyrax
import sys
import os
import argparse
import time
import prettytable


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
    clb = pyrax.connect_to_cloud_loadbalancers(dc)

    print 'Building servers in: %s' % dc

    server_details = {}
    for i in xrange(0, 2):
        host = '%s%d' % (args.base, i)
        print 'Creating server: %s' % host
        server = cs.servers.create(host, args.image, 2)
        server_details[host] = {
            'id': server.id,
            'adminPass': server.adminPass,
            'ip': '',
            'private': ''
        }
        print '%s: %s' % (host, server.id)
    complete = 0
    while complete < 2:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        for host, server in server_details.iteritems():
            if server['ip']:
                continue
            details = cs.servers.get(server['id'])
            if details.networks:
                server_details[host]['ip'] = details.networks['public']
                server_details[host]['private'] = (details.networks['private']
                                                   [0])
                complete += 1

    nodes = []
    for host, server in server_details.iteritems():
        nodes.append(clb.Node(address=server['private'], port=80,
                              condition='ENABLED'))

    vip = clb.VirtualIP(type='PUBLIC')

    lb = clb.create('%s-lb' % args.base, port=80, protocol='HTTP', nodes=nodes,
                    virtual_ips=[vip])

    public_addresses = [vip.address for vip in lb.virtual_ips]

    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    for host, server in server_details.iteritems():
        t.add_row([server['id'], host, ', '.join(server['ip']),
                   server['adminPass']])
    print 'Servers and loadbalancer online and ready...'
    print t
    t = prettytable.PrettyTable(['ID', 'Name', 'IP Address'])
    t.add_row([lb.id, lb.name, ', '.join(public_addresses)])
    print
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
