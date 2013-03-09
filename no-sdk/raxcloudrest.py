import requests
import os
import ConfigParser
import json


class RaxCloudREST:
    def __init__(self, username=None, key=None, token=None):
        self.username = username
        self.api_key = key
        self.token = token
        self.serviceCatalog = {}
        self._authUrl = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
        self.__credentials_file = os.path.expanduser(
            '~/.rackspace_cloud_credentials')

    def setusername(self, username):
        self.username = username
        self.token = None

    def set_key(self, key):
        self.api_key = key
        self.token = None

    def settoken(self, token):
        self.token = token

    def set_from_file(self):
        cfg = ConfigParser.SafeConfigParser()
        try:
            if not cfg.read(self.__credentials_file):
                raise SystemExit(Exception("The specified credential file "
                                           "'%s' does not exist"
                                           % self.__credentials_file))
        except ConfigParser.MissingSectionHeaderError as e:
            raise SystemExit(e)
        try:
            self.username = cfg.get("rackspace_cloud", "username")
            self.api_key = cfg.get("rackspace_cloud", "api_key")
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as e:
            raise SystemExit(e)

    def authenticate(self):
        if not self.username or not self.api_key:
            raise Exception('Username or API Key not provided')

        data = {
            'auth': {
                'RAX-KSKEY:apiKeyCredentials': {
                    'username': self.username,
                    'apiKey': self.api_key
                }
            }
        }

        headers, auth = self.post(self._authUrl, data)
        self.token = auth['access']['token']['id']
        self.serviceCatalog = auth['access']['serviceCatalog']

    def get(self, url, extra_headers={}):
        headers = {'Accept': 'application/json'}
        if self.token:
            headers['X-Auth-Token'] = self.token
        headers = dict(headers, **extra_headers)
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        try:
            return r.headers, r.json()
        except:
            return r.headers, r.text

    def head(self, url, extra_headers={}):
        headers = {}
        if self.token:
            headers['X-Auth-Token'] = self.token
        headers = dict(headers, **extra_headers)
        r = requests.head(url, headers=headers)
        r.raise_for_status()
        return r.headers, r.status_code

    def post(self, url, data, extra_headers={}):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.token:
            headers['X-Auth-Token'] = self.token
        headers = dict(headers, **extra_headers)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        r.raise_for_status()
        try:
            return r.headers, r.json()
        except:
            return r.headers, r.text

    def put(self, url, data=None, extra_headers={}, **kwargs):
        headers = {}
        if self.token:
            headers['X-Auth-Token'] = self.token
        headers = dict(headers, **extra_headers)
        if data:
            r = requests.put(url, headers=headers, data=data)
        else:
            r = requests.put(url, headers=headers)
        r.raise_for_status()
        return r.headers, r.status_code

    def delete(self, url, extra_headers={}):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.token:
            headers['X-Auth-Token'] = self.token
        headers = dict(headers, **extra_headers)
        r = requests.delete(url, headers=headers)
        r.raise_for_status()
        return r.headers, r.status_code

    def next_gen_svc_cat(self):
        endpoints = filter(lambda x: x['name'] == 'cloudServersOpenStack',
                           self.serviceCatalog)[0]
        return self.endpoints_to_dict(endpoints)

    def lb_svc_cat(self):
        endpoints = filter(lambda x: x['name'] == 'cloudLoadBalancers',
                           self.serviceCatalog)[0]
        return self.endpoints_to_dict(endpoints)

    def db_svc_cat(self):
        endpoints = filter(lambda x: x['name'] == 'cloudDatabases',
                           self.serviceCatalog)[0]
        return self.endpoints_to_dict(endpoints)

    def cf_svc_cat(self):
        endpoints = filter(lambda x: x['name'] == 'cloudFiles',
                           self.serviceCatalog)[0]
        return self.endpoints_to_dict(endpoints)

    def cf_cdn_svc_cat(self):
        endpoints = filter(lambda x: x['name'] == 'cloudFilesCDN',
                           self.serviceCatalog)[0]
        return self.endpoints_to_dict(endpoints)

    def dns_svc_cat(self):
        endpoints = filter(lambda x: x['name'] == 'cloudDNS',
                           self.serviceCatalog)[0]
        return self.endpoints_to_string(endpoints)

    def endpoints_to_dict(self, endpoints):
        cat = {}
        for endpoint in endpoints['endpoints']:
            cat[endpoint['region']] = endpoint['publicURL']
        return cat

    def endpoints_to_string(self, endpoints):
        return endpoints['endpoints'][0]['publicURL']

# vim:set ts=4 sw=4 expandtab:
