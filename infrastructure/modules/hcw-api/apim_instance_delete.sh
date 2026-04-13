#!/bin/bash

environment_name=$1
apim_environment=$2
apim_private_key_secret_arn=$3

source ./modules/hcw-api/proxygen-profiles.sh


if [[ "$environment_name" == pr-* ]]; then
  env_name_suffix="_${environment_name}"
  echo "Set env name suffix to ${env_name_suffix}"
else
  env_name_suffix=""
  echo "No name suffix set"
fi

if [[ "$environment_name" == "prod" ]]; then
  source ./modules/hcw-api/proxygen-setup.sh \
    "$apim_private_key_secret_arn" \
    "$PROD_PROXYGEN_ENDPOINT_URL" \
    "$PROD_PROXYGEN_BASE_URL" \
    "$PROD_PROXYGEN_KEY_ID" \
    "$PROD_PROXYGEN_CLIENT_ID"
else
  source ./modules/hcw-api/proxygen-setup.sh \
    "$apim_private_key_secret_arn" \
    "$PTL_PROXYGEN_ENDPOINT_URL" \
    "$PTL_PROXYGEN_BASE_URL" \
    "$PTL_PROXYGEN_KEY_ID" \
    "$PTL_PROXYGEN_CLIENT_ID"
fi

# Deploy proxygen instance
echo proxygen instance delete --no-confirm "$apim_environment" "healthcare-worker${env_name_suffix}"
proxygen instance delete --no-confirm "$apim_environment" "healthcare-worker${env_name_suffix}"

echo "Delete triggered"
