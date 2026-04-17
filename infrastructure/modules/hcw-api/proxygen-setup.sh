#!/bin/bash

set -e

apim_private_key_secret_id=$1
endpoint_url=$2
base_url=$3
key_id=$4
client_id=$5

yes "" | proxygen credentials set
proxygen settings set api "healthcare-worker-api"
proxygen settings set endpoint_url "$endpoint_url"
proxygen settings set spec_output_format "yaml"

proxygen credentials set base_url "$base_url"

# Get proxygen private key to allow for proxy instance deployment
aws secretsmanager get-secret-value --secret-id "$apim_private_key_secret_id" | jq -r ".SecretString" > /tmp/proxygen_private_key.pem
proxygen credentials set private_key_path /tmp/proxygen_private_key.pem key_id "$key_id" client_id "$client_id"
