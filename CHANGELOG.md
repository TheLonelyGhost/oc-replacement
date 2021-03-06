# Changelog

We follow [Semantic Versioning](http://semver.org/) as a way of measuring stability of an update. This
means we will never make a backwards-incompatible change within a major version of the project.

## [0.3.3] - 2019-11-22

- Fixes stack trace when `current-context:` yaml fragment is not part of the same file as the list of contexts

## [0.3.2] - 2019-11-07

- Fixes typo in source code misspelling one of the properties we're trying to log the value of

## [0.3.1] - 2019-11-07

- Missing `--verbose` flag to crank up the logging
- Adds more logging statements for later troubleshooting, if need be

## [0.3.0] - 2019-11-07

- Uses the TLS verification settings already present in the kube config
- Adds missing Windows support (path separation is different)

## [0.2.0] - 2019-10-25

- Adds support for `KUBECONFIG` environment variable
- Supports multiple kube configs and keeping data altered in the same location it came from

## [0.1.0] - 2019-10-15

- Initial release
