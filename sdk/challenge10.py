#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Matt Martz
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import pyrax
import sys
import os
import argparse
import time
import prettytable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base hostname to use')
    parser.add_argument('--domain', help='The domain to create the DNS record '
                        'in', required=True)
    parser.add_argument('--sshkey', help='The SSH key to upload be placed at'
                        '/root/.ssh/authorized_keys', required=True)
    parser.add_argument('--dc', required=False, help='The region to '
                        'build the servers in', choices=['DFW', 'ORD', 'LON'],
                        default=pyrax.default_region)
    parser.add_argument('--image', required=False, help='The image ID to build'
                        ' the servers with',
                        default='5cebb13a-f783-4f8c-8058-c4182c724ccd')
    parser.add_argument('--flavor', required=False, help='The flavor ID to'
                        ' build the servers with',
                        default=2, type=int)
    parser.add_argument('--count', required=False, help='Number of servers to '
                        'build. Default 2', default=2, type=int)
    parser.add_argument('--error-page', required=False, help='Path to an html'
                        ' file to be used as the custom error page on the'
                        ' laod balancer')
    parser.add_argument('--container', required=False, help='Cloud files '
                        'container to backup the custom error page to. '
                        'Defaults to [BASE].[DOMAIN]')

    args = parser.parse_args()
    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers
    dns = pyrax.cloud_dns
    cf = pyrax.cloudfiles

    parts = args.domain.split('.')
    if len(parts) < 2:
        raise SystemExit('Not a proper domain: %s' % args.domain)

    print 'Building servers in: %s' % args.dc

    try:
        with open(os.path.expanduser(args.sshkey)) as f:
            sshkey = f.read()
        if 'PRIVATE KEY' in sshkey:
            raise SystemExit('Please provide a public key, key provided was'
                             ' a private key')
    except IOError:
        raise SystemExit('SSH Key does not exist: %s' % args.sshkey)
    servers = {}
    for i in xrange(0, args.count):
        host = '%s%d' % (args.base, i)
        print 'Creating server: %s' % host
        servers[host] = cs.servers.create(host, args.image, args.flavor,
                                          files={'/root/.ssh/authorized_keys':
                                                 sshkey})
        print '%s: %s' % (host, servers[host].id)
    statuses = ['ACTIVE', 'ERROR', 'UNKNOWN']
    progress = []
    print 'Sleeping 30 seconds before checking server build progress...'
    print '\n' * (abs(args.count) - 1)
    while filter(lambda server: server.status not in statuses,
                 servers.values()):
        time.sleep(30)
        progress[:] = []
        for host in servers:
            if servers[host].status in statuses:
                progress.append('%s: %s%%' % (host, servers[host].progress))
                continue
            servers[host].get()
            progress.append('%s: %s%%' % (host, servers[host].progress))
        progress.sort()
        sys.stdout.write('\r%s%s' % ('\x1b[A' * (len(progress) - 1),
                         '\n'.join(progress)))
        sys.stdout.flush()

    active = (len(filter(lambda server: server.status == 'ACTIVE',
                         servers.values())))
    if not active:
        raise SystemExit('\nNo servers built successfully')
    elif active != args.count:
        print '\nNot all servers successfully built'

    print '\n\nBuilding load balancer'
    nodes = []
    for host, server in servers.iteritems():
        if server.status != 'ACTIVE':
            print 'Not adding %s to LB as it did not build' % host
            continue
        nodes.append(clb.Node(address=server.networks['private'][0], port=80,
                              condition='ENABLED'))

    vip = clb.VirtualIP(type='PUBLIC')

    lb = clb.create('%s-lb' % args.base, port=80, protocol='HTTP', nodes=nodes,
                    virtual_ips=[vip])
    print '%s: %s' % (lb.name, lb.id)

    lb = pyrax.utils.wait_until(lb, 'status', ['ACTIVE'], interval=30,
                                verbose=True)
    if not lb:
        raise SystemExit('Load balancer failed to build')

    public_addresses = [vip.address for vip in lb.virtual_ips]

    print 'Adding HTTP health check...'
    lb.add_health_monitor(type='HTTP', delay=1, timeout=3,
                          attemptsBeforeDeactivation=2, path='/',
                          statusRegex="^[23][0-9][0-9]$",
                          bodyRegex='</html>',
                          hostHeader='%s.%s' % (args.base, args.domain))

    lb = pyrax.utils.wait_until(lb, 'status', ['ACTIVE'], attempts=20,
                                verbose=True)

    default_error_page = """<html>
<head>
    <title>ErRAWR!</title>
</head>
<body>
    <h1>Oops, ErRAWR!</h1>
</body>
</html>"""
    if args.error_page:
        try:
            with open(args.error_page) as f:
                error_content = f.read()
        except IOError:
            error_content = default_error_page
    else:
        error_content = default_error_page
    print 'Adding custom error page...'
    lb.set_error_page(error_content)

    domains = dns.list()
    try:
        dom = filter(lambda x: x.name == args.domain, domains)[0]
    except IndexError:
        raise SystemExit('No matching domains: %s' % args.domain)

    records = []
    for public_address in public_addresses:
        rec_type = 'AAAA' if ':' in public_address else 'A'
        records.append({
            'ttl': 300,
            'name': '%s.%s' % (args.base, args.domain),
            'type': rec_type,
            'data': public_address
        })

    domain = dom.add_records(records)
    print ('Record(s) added: %s -> %s' % ('%s.%s' % (args.base, args.domain),
                                          ', '.join(public_addresses)))

    if args.container:
        container = args.container
    else:
        container = '%s.%s' % (args.base, args.domain)

    print ('Backing up custom error page (%s) to container %s' %
           ('%s-error.html' % ('%s.%s' % (args.base, args.domain)), container))
    try:
        cont = cf.get_container(container)
    except pyrax.exceptions.NoSuchContainer as e:
        print 'Container %s does not exist, creating...' % container
        cont = cf.create_container(container)

    cont.store_object('%s-error.html' % ('%s.%s' % (args.base, args.domain)),
                      error_content, content_type='text/html')

    t = prettytable.PrettyTable(['ID', 'Host', 'Status', 'IP',
                                 'Admin Password'])
    for host, server in servers.iteritems():
        t.add_row([server.id, host, server.status,
                   ', '.join(server.networks['public']), server.adminPass])
    print 'Servers and loadbalancer online and ready...'
    print t
    t = prettytable.PrettyTable(['ID', 'Host', 'Name', 'IP Address'])
    t.add_row([lb.id, '%s.%s' % (args.base, args.domain), lb.name,
               ', '.join(public_addresses)])
    print
    print t


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
