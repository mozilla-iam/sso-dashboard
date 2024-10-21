#!/bin/sh
set -eu

if [ -f "$TOX_ENV_DIR/bin/node" ]; then
    echo Node and friends already installed.
    npm ci
    exit 0
fi

nodeenv --prebuilt -p --node "$NODE_VERSION" "$TOX_ENV_DIR"
npm install -g "npm@$NPM_VERSION"
npm ci
