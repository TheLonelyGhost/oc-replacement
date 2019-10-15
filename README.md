# OC Replacement

This is a small python tool to replace parts of RedHat's CLI tool for OpenShift, `oc`.

## Setup

Required:

- Python 3.x
- pip
- [pipx](https://github.com/pipxproject/pipx) (optional)

```shell
# If using pipx
$ pipx install oc-replacement

# If not
$ python3 -m pip install oc-replacement
```

## Authentication

The simplest example is if you already have an OpenShift cluster setup and need to refresh a bearer token. You can either specify the context with `--context my-context`, or not pass it in order to use the current context. `oc-auth` reads the given (or implied) context and figured out which credential is used for that context, choosing to reauth against the context's linked cluster to refresh the token.

```shell
$ oc-auth --username 'my-username' --password 'hunter2'
```
