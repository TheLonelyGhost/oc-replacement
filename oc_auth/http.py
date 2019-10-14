import logging
import os

from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session
import requests


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class OpenshiftHttp(OAuth2Session):
    """
    Wrapper for a requests session object with our project-specific settings
    """

    def __init__(self, server, username, password, *args, **kwargs):
        r = requests.get('{server}/.well-known/oauth-authorization-server'.format(server=server), verify=False)
        r.raise_for_status()
        self.config = r.json()

        self.base_uri = self.config['issuer']
        self.oauth_redirect_url = '{server}/token/implicit'.format(server=self.config['issuer'].rstrip('/'))

        client = MobileApplicationClient(client_id='openshift-challenging-client')

        self.verify = False
        super(OpenshiftHttp, self).__init__(client=client, scope=self.config['scopes_supported'], *args, **kwargs)

        self._login(username, password)
        logging.info(self.token)

        self.headers.update({'Accept': 'application/json',
                             'Content-Type': 'application/json',
                             'User-Agent': 'David Alexander: "Too lazy... Just script it..."'})

    def prepare_request(self, request, **kwargs):
        if request.url.startswith('/'):
            # Insert our github.com api string as the base
            request.url = self.base_uri + request.url

        return super(OpenshiftHttp, self).prepare_request(request, **kwargs)

    def _login(self, username, password):
        auth_url, state = self.authorization_url(self.config['authorization_endpoint'])
        r = self.get(auth_url, verify=False, auth=(username, password))
        self.token_info = self.token_from_fragment(r.url)
        self.token = self.token_info['access_token']
