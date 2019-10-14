import codecs
import os

from setuptools import find_packages, setup

from oc_auth import __version__


def long_description():
    if not (os.path.isfile('README.rst') and os.access('README.rst', os.R_OK)):
        return ''

    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()


testing_deps = [
    'pytest',
    'pytest-cov',
]
dev_helper_deps = [
    'better-exceptions',
]


setup(
    name='oc-replacement',
    version=__version__,
    description='A replacement for the OAuth flow for interacting with OpenShift-based Kubernetes clusters',
    long_description=long_description(),
    url='https://github.com/thelonelyghost/oc-auth',
    author='David Alexander',
    author_email='opensource@thelonelyghost.com',
    license='MIT',
    classifiers=[
        'Development Status :: 1 - Planning',

        'Intended Audience :: End Users/Desktop',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='',
    packages=find_packages(exclude=['test', 'test.*', '*.test', '*.test.*']),
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'oc-auth = oc_auth.cli.main:main',
        ],
    },
    extras_require={
        'dev': testing_deps + dev_helper_deps,
    },
    tests_require=testing_deps,
    install_requires=[
        'ruamel.yaml',
        'requests',
        'requests-oauthlib',
    ],
)
