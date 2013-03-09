#!/usr/bin/env python

import raxcloudrest
import sys
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
    rax = raxcloudrest.RaxCloudREST()
    rax.set_from_file()
    rax.authenticate()
    endpoints = rax.next_gen_svc_cat()
    dc = args.dc if args.dc else endpoints.keys()[0]
    endpoint = endpoints.get(dc)
    print 'Building servers in: %s' % dc
    server_details = {}
    for i in xrange(0, 3):
        host = '%s%d' % (args.base, i)
        data = {
            'server': {
                'flavorRef': '2',
                'imageRef': args.image,
                'name': host,
            }
        }
        print 'Creating server: %s' % host
        headers, server = rax.post('%s/servers' % endpoint, data)
        server_details[host] = {
            'id': server['server']['id'],
            'adminPass': server['server']['adminPass'],
            'ip': ''
        }
        print '%s: %s' % (host, server['server']['id'])
    complete = 0
    while complete < 3:
        print 'Sleeping 30 seconds before checking for server readiness...'
        time.sleep(30)
        for host, server in server_details.iteritems():
            headers, details = rax.get('%s/servers/%s' %
                                       (endpoint, server['id']))
            if details['server']['status'] == 'ACTIVE':
                server_details[host]['ip'] = details['server']['accessIPv4']
                complete += 1
    t = prettytable.PrettyTable(['ID', 'Host', 'IP', 'Admin Password'])
    for host, server in server_details.iteritems():
        t.add_row([server['id'], host, server['ip'], server['adminPass']])
    print 'Servers online and ready...'
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
