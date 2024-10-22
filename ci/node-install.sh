#!/bin/sh
# Meant to be used with tox. Probably don't use this normally.

set -eu

# If node isn't installed, install it using nodeenv (along with npm).
if [ ! -f "$TOX_ENV_DIR/bin/node" ] || [ "$("$TOX_ENV_DIR/bin/node" --version)" != "v$NODE_VERSION" ]; then
    nodeenv --prebuilt -p --node "$NODE_VERSION" --with-npm --npm "$NPM_VERSION" "$TOX_ENV_DIR"
fi

# Ensure npm is the version we want.
if [ "$("$TOX_ENV_DIR/bin/npm" --version)" != "$NPM_VERSION" ]; then
    npm install -g "npm@$NPM_VERSION"
fi

npm ci
