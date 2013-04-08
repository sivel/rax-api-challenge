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
import random
import socket
import struct
import re
from OpenSSL import crypto, SSL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base', help='The base hostname to use')
    parser.add_argument('--domain', help='The domain to create the DNS record '
                        'in', required=True)
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
                        'build. Default 3', default=3, type=int)
    parser.add_argument('--network', required=False, help='The network to'
                        ' create the servers in. Will create the network if it'
                        ' does not exist. Defaults to 192.168.133.0/24. A CIDR'
                        ' of 24 is assumed if a CIDR is not supplied or an'
                        ' invalid CIDR is specified',
                        default='192.168.133.0/24')

    parser.add_argument('-b', '--bits', help='Number of bits to use in '
                        'generating the private key, in multiples of 1024',
                        type=int, default=1024)

    encryption = parser.add_mutually_exclusive_group()
    encryption.add_argument('-t', '--type', help='Encryption type to use in'
                            ' generating the private key. Default RSA',
                            choices=('RSA', 'DSA'), default='RSA')
    encryption.add_argument('--rsa', help='Set encryption type to RSA for use'
                            ' when generating the private key',
                            action='store_const', const='RSA', dest='type')
    encryption.add_argument('--dsa', help='Set encryption type to DSA for use'
                            ' when generating the private key',
                            action='store_const', const='DSA', dest='type')

    parser.add_argument('-c', '--country', help='Set the Country/C option in'
                        ' the generation of the certificate')
    parser.add_argument('-s', '--state', help='Set the State/Province/ST'
                        ' option in the generation of the certificate')
    parser.add_argument('-l', '--locality', help='Set the Locality/City/L in'
                        ' the generation of the certificate')
    parser.add_argument('-o', '--organization', help='Set the Organization/O'
                        ' option in the generation of the certificate')
    parser.add_argument('-u', '--unit', help='Set the Organizational Unit/OU'
                        ' option in the generation of the certificate')
    parser.add_argument('-n', '--common-name', help='Set the Common Name/CN'
                        ' option in the generation of the certificate')
    parser.add_argument('-e', '--expire', help='Length in days before the'
                        ' certificate expires. Default 365', type=int,
                        default=365)
    parser.add_argument('--serial', help='Set the serial number of the'
                        ' certificate, defaults to a randomly generated number'
                        ' between 1 and 1,000,000', type=int)
    parser.add_argument('--digest', help='Set certificate signing digest type.'
                        ' Default sha1', choices=('sha1', 'md5'),
                        default='sha1')

    args = parser.parse_args()

    netid = args.network.split('/', 1)
    if not re.match('^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                    '(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
                    str(netid[0])):
        raise SystemExit('Not a proper IP: %s' % netid[0])
    quad1, quad2, quad3, quad4 = netid[0].split('.')
    if ((int(quad1) not in (10, 172, 192)) or
            (int(quad1) == 172 and int(quad2) not in xrange(16, 32)) or
            (int(quad1) == 192 and int(quad2) != 168)):
        raise SystemExit('An appropriate RFC 1918 (private ip) was not'
                         ' provided')

    if len(netid) != 2:
        mask = 24
    elif netid[1].count('/') != 0:
        mask = 24
    elif ((int(quad1) == 192 and int(netid[1]) < 16) or
          (int(quad1) == 172 and int(netid[1]) < 12) or
          (int(quad1) == 10 and int(netid[1]) < 8)):
        mask = 24
    else:
        mask = int(netid[1])

    if not args.bits or args.bits % 1024:
        raise SystemExit('Bits must be a multiple of 1024. %d provided'
                         % args.bits)

    for attr in ('country', 'state', 'locality', 'organization', 'unit',
                 'common_name'):
        while not getattr(args, attr):
            val = raw_input('%s: ' % attr.replace('_', ' ').title()).strip()
            setattr(args, attr, val)

    key = generate_key(**vars(args))
    cert = generate_cert(key, **vars(args))
    key_string = dump_key(key)
    cert_string = dump_cert(cert)

    credentials_file = os.path.expanduser('~/.rackspace_cloud_credentials')
    pyrax.set_credential_file(credentials_file, region=args.dc)
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers
    dns = pyrax.cloud_dns
    cf = pyrax.cloudfiles
    cnw = pyrax.cloud_networks
    cbs = pyrax.cloud_blockstorage

    parts = args.domain.split('.')
    if len(parts) < 2:
        raise SystemExit('Not a proper domain: %s' % args.domain)

    print 'Operating in: %s' % args.dc

    networks = cnw.list()
    for network in networks:
        if getattr(network, 'cidr'):
            if address_in_network(netid[0], network.cidr):
                cidr = int(network.cidr.split('/')[1])
                if cidr != mask:
                    print ('The provided IP (%s) falls within %s, using %s:%s'
                           % (netid[0], network.cidr, network.label,
                              network.cidr))
                break
        network = None

    if not network:
        print 'No matching networks found, creating %s/%s' % (netid[0], mask)
        network = cnw.create('%s-net' % args.base,
                             cidr='%s/%s' % (netid[0], mask))
    else:
        print 'Matching network found: %s:%s' % (network.label, network.cidr)
    networks = network.get_server_networks(public=True, private=True)

    servers = {}
    cbses = {}
    for i in xrange(0, args.count):
        host = '%s%d' % (args.base, i)
        print 'Creating server: %s' % host
        servers[host] = cs.servers.create(host, args.image, args.flavor,
                                          nics=networks)
        print '%s: %s' % (host, servers[host].id)
        print 'Creating CBS for %s' % host
        cbses[host] = cbs.create(name='%s-cbs' % host, size=100,
                                 volume_type="SATA")
        print '%s-cbs: %s' % (host, cbses[host].id)

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

    print '\n\nAttaching CBS volumes to servers'
    for host, vol in cbses.iteritems():
        print 'Attaching %s to %s' % (vol.display_name, host)
        vol.attach_to_instance(servers[host], mountpoint='/dev/xvdb')

    print 'Building load balancer'
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

    lb.add_ssl_termination(
        securePort=443,
        enabled=True,
        secureTrafficOnly=False,
        certificate=cert_string,
        privatekey=key_string,
    )

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


def generate_key(**kwargs):
    key = crypto.PKey()
    if kwargs.get('type') == 'RSA':
        key_type = crypto.TYPE_RSA
    else:
        key_type = crypto.TYPE_DSA
    key.generate_key(key_type, kwargs.get('bits'))
    return key


def generate_cert(key, **kwargs):
    cert = crypto.X509()

    subject = cert.get_subject()
    subject.C = kwargs.get('country')
    subject.ST = kwargs.get('state')
    subject.L = kwargs.get('locality')
    subject.O = kwargs.get('organization')
    subject.OU = kwargs.get('unit')
    subject.CN = kwargs.get('common_name')

    cert.set_serial_number(kwargs.get('serial') if kwargs.get('serial') else
                           random.choice(xrange(1, 1000000)))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(kwargs.get('expire') * 24 * 60 * 60)
    cert.set_issuer(subject)
    cert.set_pubkey(key)
    cert.sign(key, kwargs.get('digest'))

    return cert


def dump_key(key):
    return crypto.dump_privatekey(crypto.FILETYPE_PEM, key)


def dump_cert(cert):
    return crypto.dump_certificate(crypto.FILETYPE_PEM, cert)


def address_in_network(ip, net):
    ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
    netstr, bits = net.split('/')
    netaddr = int(''.join(['%02x' % int(x) for x in netstr.split('.')]), 16)
    mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
    return (ipaddr & mask) == (netaddr & mask)


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
