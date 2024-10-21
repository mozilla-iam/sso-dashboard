#!/bin/sh
set -eu

if [ -f "$TOX_ENV_DIR/bin/node" ]; then
    echo Node and friends already installed.
    exit 0
fi

nodeenv --prebuilt -p --node 18.20.4 "$TOX_ENV_DIR"
npm install -g npm@latest
npm ci
