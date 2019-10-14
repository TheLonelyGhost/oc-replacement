from oauthlib.oauth2 import MobileApplicationClient
import requests
from requests_oauthlib import OAuth2Session


class OpenshiftHttp(OAuth2Session):
    """
    Wrapper for a requests session object with our project-specific settings
    """

    verify = True

    def __init__(self, *args, **kwargs):
        self.__config = {}

        super(OpenshiftHttp, self).__init__(client=MobileApplicationClient(client_id='openshift-challenging-client'), *args, **kwargs)

        self.headers.update({'Accept': 'application/json',
                             'Content-Type': 'application/json',
                             'User-Agent': 'David Alexander: "Too lazy... Just script it..."'})

    def prepare_request(self, request, **kwargs):
        if request.url.startswith('/'):
            request.url = self.base_uri + request.url

        return super(OpenshiftHttp, self).prepare_request(request, **kwargs)

    def build_client(self, server, username, password):
        self._populate_default_config(server)
        self._login(username, password)

    def _populate_default_config(self, server):
        r = requests.get('{}/.well-known/oauth-authorization-server'.format(server), verify=OpenshiftHttp.verify)
        r.raise_for_status()
        self.__config = r.json()

        self.scope = self.__config['scopes_supported']
        self.base_uri = self.__config['issuer']

    def _login(self, username, password):
        auth_url, state = self.authorization_url(self.__config['authorization_endpoint'])
        r = self.get(auth_url, auth=(username, password), verify=OpenshiftHttp.verify)

        self.token = self.token_from_fragment(r.url)
