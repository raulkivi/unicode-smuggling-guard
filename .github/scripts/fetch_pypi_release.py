"""Download the files PyPI serves for release $TAG into dist/, verifying PyPI's SHA-256.

Signing what PyPI actually serves (not a rebuild) means the signatures cover
exactly what users install.
"""

import hashlib
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

PROJECT = 'unicode-smuggling-guard'
PYPI_FILES = 'https://files.pythonhosted.org/'
ATTEMPTS, WAIT_SECONDS = 20, 15  # PyPI's JSON API can lag a publish by a minute or two.


def release_files(version):
    url = f'https://pypi.org/pypi/{PROJECT}/{version}/json'
    for _ in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(url) as response:  # noqa: S310 - fixed https URL
                files = json.load(response)['urls']
            if files:
                return files
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        time.sleep(WAIT_SECONDS)
    sys.exit(f'{PROJECT} {version} not found on PyPI')


def main():
    tag = os.environ['TAG']
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        sys.exit(f'not a release tag: {tag!r}')
    out = pathlib.Path('dist')
    out.mkdir(exist_ok=True)
    for f in release_files(tag[1:]):
        # Only PyPI's own file host; the URL comes from an API response, not from us.
        if not f['url'].startswith(PYPI_FILES):
            sys.exit(f"unexpected download URL: {f['url']!r}")
        with urllib.request.urlopen(f['url']) as response:  # noqa: S310 - scheme and host checked above
            data = response.read()
        if hashlib.sha256(data).hexdigest() != f['digests']['sha256']:
            sys.exit(f"SHA-256 mismatch for {f['filename']}")
        (out / f['filename']).write_bytes(data)
        print(f['filename'])


if __name__ == '__main__':
    main()
