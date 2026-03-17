#!/bin/bash

# Cleanup previous builds
rm -rf hcw_api-*

poetry install
poetry build

cd dist || exit
tar -xvf hcw_api-*.tar.gz

cd hcw_api-*/src || exit
mkdir -p specification/components/examples
cp ../../../specification/components/examples/*.json specification/components/examples/
zip -r ../../../hcw-api.zip . -x "*.pyc" -x "*__pycache__*"
