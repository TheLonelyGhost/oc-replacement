import logging
import os
import urllib3

from ruamel import yaml
from typing import Dict, Union
import requests

from .. import __version__
from ..http import OpenshiftHttp

from ._base import MyParser


User = Dict[str, Union[Dict[str, str], str]]
Context = Dict[str, Union[Dict[str, str], str]]
Cluster = Dict[str, Union[Dict[str, str], str]]
_missing = object()


def get_args():
    p = MyParser()
    p.add_argument('--version', '-v', action='version', help='Prints the program version and exits', version='%(prog)s' + __version__)

    p.add_argument('--username', '-u', action='store', required=True, dest='username')
    p.add_argument('--password', '-p', action='store', required=True, dest='password')

    p.add_argument('--context', action='store', dest='context', default=_missing,
                   help='The name of the kubectl context for which to refresh the credential in ~/.kube/config (Default: currently selected context)')

    p.add_argument('--cluster', action='store', dest='cluster', default='default',
                   help='The name of the cluster in ~/.kube/config against which to authenticate (OPTIONAL)')
    p.add_argument('--credential', action='store', dest='cred', default='default',
                   help='The name of the credential in ~/.kube/config to update (OPTIONAL)')

    p.add_argument('--insecure', action='store_const', dest='verify', const=False, default=True)

    return p.parse_args()


def get_context_mapping(kube_config, name=None, cluster=None, credential=None) -> Context:
    if name == _missing:
        name = kube_config.get('current-context')

    if name:
        for context in kube_config['contexts']:
            if context['name'] == name:
                return context

        if cluster and credential:
            context = {
                'name': name,
                'context': {
                    'cluster': cluster,
                    'namespace': 'default',
                    'user': credential,
                },
            }
            logging.warning('Missing kubectl context {!r}. Creating it from the info given'.format(name))
            kube_config['contexts'].append(context)

    raise RuntimeError('No context {!r} found in ~/.kube/config'.format(name))


def get_user(kube_config, name) -> User:
    for user in kube_config['users']:
        if user['name'] == name:
            return user

    user = {
        'name': name,
        'user': {
            'token': '',
        },
    }
    kube_config['users'].append(user)
    return user


def get_cluster(kube_config, name) -> Cluster:
    for cluster in kube_config['clusters']:
        if cluster['name'] == name:
            return cluster

    raise RuntimeError('No cluster {!r} found in ~/.kube/config'.format(name))


def main():
    logging.basicConfig(level=logging.INFO)
    opts = get_args()

    if not opts.verify:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        requests.packages.urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
        logging.warning('Disabled TLS verification')
        OpenshiftHttp.verify = False

    with open(os.path.expanduser('~/.kube/config'), 'r', encoding='utf-8') as f:
        kube_config = yaml.load(f, Loader=yaml.RoundTripLoader)

    if opts.cred and opts.cluster:
        context = get_context_mapping(kube_config, opts.context)
    else:
        context = get_context_mapping(kube_config, opts.context)

    user = get_user(kube_config, context['context']['user'])
    cluster = get_cluster(kube_config, context['context']['cluster'])

    http = OpenshiftHttp()
    http.build_client(server=cluster['cluster']['server'], username=opts.username, password=opts.password)

    user['user']['token'] = http.token['access_token']
    if not user['name']:
        user['name'] = '{user}/auth'.format(user=opts.username)

    with open(os.path.expanduser('~/.kube/config'), 'w', encoding='utf-8') as f:
        yaml.dump(kube_config, f, Dumper=yaml.RoundTripDumper)


if __name__ == '__main__':
    main()
