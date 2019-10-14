import argparse
import sys

from oc_auth.http import OpenshiftHttp


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('ERROR: %s\n\n' % message)
        self.print_help()
        sys.exit(2)


def create_client(username, password):
    if not username:
        raise KeyError('Requires username to be given via OC_USER variable or command line flag')
    if not password:
        raise KeyError('Requires password to be given via OC_PASS variable or command line flag')

    return OpenshiftHttp(username=username, password=password)
