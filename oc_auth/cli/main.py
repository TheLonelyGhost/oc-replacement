import logging
import os
import urllib3

from typing import Dict, Union
import requests

from .. import __version__
from ..http import OpenshiftHttp
from ..kube_config import KubeConfig, KubeConfigDataSnippet

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
    p.add_argument('--verbose', action='store_const', dest='log_level', const=logging.DEBUG, default=logging.INFO)

    return p.parse_args()


def get_context_mapping(kube_config: KubeConfig, name=_missing, cluster=None, credential=None) -> KubeConfigDataSnippet:
    if name is _missing:
        name = kube_config.data.value.get('current-context')

    if name:
        for config in kube_config.each_config():
            if 'contexts' not in config.value:
                continue
            for context in config.value['contexts']:
                if context['name'] == name:
                    return KubeConfigDataSnippet(parent=config, data=context)

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
            for config in kube_config.each_config():
                config.value['contexts'].append(context)
                return KubeConfigDataSnippet(parent=config, data=context)

    raise RuntimeError('No context {!r} found in ~/.kube/config'.format(name))


def get_user(kube_config: KubeConfig, name: str) -> KubeConfigDataSnippet:
    for config in kube_config.each_config():
        if 'users' not in config.value:
            continue
        for user in config.value['users']:
            if user['name'] == name:
                return KubeConfigDataSnippet(parent=config, data=user)

    user = {
        'name': name,
        'user': {
            'token': '',
        },
    }
    logging.warning('Missing kubectl user {!r}. Creating it from the info given'.format(name))
    for config in kube_config.each_config():
        if 'users' not in config.value:
            config.value['users'] = []
        config.value['users'].append(user)
        config.is_dirty = True
        return KubeConfigDataSnippet(parent=config, data=user)

    raise RuntimeError('No user {!r} found in ~/.kube/config'.format(name))


def get_cluster(kube_config: KubeConfig, name: str) -> KubeConfigDataSnippet:
    for config in kube_config.each_config():
        if 'clusters' not in config.value:
            continue
        for cluster in config.value['clusters']:
            if cluster['name'] == name:
                return KubeConfigDataSnippet(parent=config, data=cluster)

    raise RuntimeError('No cluster {!r} found in ~/.kube/config'.format(name))


def disable_tls_verification():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    requests.packages.urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
    logging.warning('Disabled TLS verification')
    OpenshiftHttp.verify = False


def main():
    opts = get_args()
    logging.basicConfig(level=opts.log_level, format='%(levelname)s: %(message)s')
    logging.debug('Given context: {}'.format(opts.context))
    logging.debug('Given cluster: {}'.format(opts.cluster))
    logging.debug('Given credential: {}'.format(opts.cred))
    logging.debug('Given TLS verification: {}'.format('yes' if opts.verify else 'no'))

    kube_config = KubeConfig.find_from_env()

    context = get_context_mapping(kube_config, opts.context)
    user = get_user(kube_config, context.value['context']['user'])
    cluster = get_cluster(kube_config, context.value['context']['cluster'])

    if not opts.verify:
        disable_tls_verification()
    elif cluster.value['cluster'].get('insecure-skip-tls-verify'):
        disable_tls_verification()

    http = OpenshiftHttp()
    http.build_client(server=cluster.value['cluster']['server'], username=opts.username, password=opts.password)

    user.value['user']['token'] = http.token['access_token']
    user.is_dirty = True
    if not user.value['name']:
        user.value['name'] = '{user}/auth'.format(user=opts.username)
        user.is_dirty = True

    kube_config.persist(context)
    kube_config.persist(user)
    kube_config.persist(cluster)


if __name__ == '__main__':
    main()
