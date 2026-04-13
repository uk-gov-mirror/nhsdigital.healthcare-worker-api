#!/bin/bash

set -e

environment_name=$1
apim_environment=$2
apim_private_key_secret_arn=$3
api_gw_url=$4
spec_publish_private_key_secret_arn=$5

source ./modules/hcw-api/proxygen-profiles.sh

cp ../specification/healthcare-worker-api.yaml temp_spec.yaml

# If a pre-bundled resolved spec exists (produced by the deploy buildspec pre_build step),
# use it so that all externalValue references (e.g. JSON example files) are inlined.
# This ensures proxygen receives a fully self-contained spec with no local file dependencies.
if [ -f "../specification/healthcare-worker-api.resolved.yaml" ]; then
  echo "Using pre-bundled resolved spec (healthcare-worker-api.resolved.yaml)"
  cp ../specification/healthcare-worker-api.resolved.yaml temp_spec.yaml
else
  echo "Warning: resolved spec not found, falling back to original (externalValue references will not be inlined)"
  cp ../specification/healthcare-worker-api.yaml temp_spec.yaml
fi

# Stamp version into spec (replace placeholder with short commit SHA)
short_sha=${CODEBUILD_RESOLVED_SOURCE_VERSION:0:8}
sed -i "s/__VERSION__/${short_sha}/g" temp_spec.yaml

yq -i ".x-nhsd-apim.target.url = \"${api_gw_url}\"" temp_spec.yaml
if [[ "$environment_name" == pr-* ]]; then
  uppercase_env_name=$(echo "$environment_name" | tr '[:lower:]' '[:upper:]')
  yq -i ".info.title = \"[${uppercase_env_name}] Healthcare Worker API\"" temp_spec.yaml
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
service_base_path="healthcare-worker${env_name_suffix}"
echo proxygen instance deploy --no-confirm "$apim_environment" "${service_base_path}" ./temp_spec.yaml
proxygen instance deploy --no-confirm "$apim_environment" "${service_base_path}" ./temp_spec.yaml

if [[ "$environment_name" == "ft" ]]; then
  echo "Uploading app spec to UAT"
  source ./modules/hcw-api/proxygen-setup.sh \
    "$spec_publish_private_key_secret_arn" \
    "$PROD_PROXYGEN_ENDPOINT_URL" \
    "$PROD_PROXYGEN_BASE_URL" \
    "$PROD_PROXYGEN_KEY_ID" \
    "$PROD_PROXYGEN_CLIENT_ID"
  proxygen spec publish ./temp_spec.yaml --uat --no-confirm
elif [[ "$environment_name" == "int" ]]; then
  echo "Uploading app spec"
  source ./modules/hcw-api/proxygen-setup.sh \
    "$spec_publish_private_key_secret_arn" \
    "$PROD_PROXYGEN_ENDPOINT_URL" \
    "$PROD_PROXYGEN_BASE_URL" \
    "$PROD_PROXYGEN_KEY_ID" \
    "$PROD_PROXYGEN_CLIENT_ID"
  proxygen spec publish ./temp_spec.yaml --no-confirm
fi

# We only want to perform these steps for PRs, they're not required for static environments (and won't work in nhsd-prod)
if [[ "$environment_name" == pr-* ]]; then
  echo "Creating APIM proxy app for new PR env"
  access_token=$(proxygen pytest-nhsd-apim get-token | jq -r ".pytest_nhsd_apim_token")

  org=nhsd-nonprod
  app_details=$(curl --location "https://api.enterprise.apigee.com/v1/organizations/${org}/developers/ian.robinson27@nhs.net/apps/${service_base_path}" \
    --header "Authorization: Bearer ${access_token}" \
    --header 'Content-Type: application/json')
  existing_app_id=$(echo "$app_details" | jq -r ".appId")

  if [[ "$existing_app_id" != "null" ]]; then
    echo "App already created, checking if the api product is still linked"
    api_product=$(echo "$app_details" | jq -r ".credentials[0].apiProducts")
    if [[ "$api_product" == "[]" ]]; then
        echo "The API product has been removed, so we need to remove and re-create the app"
        curl --location "https://api.enterprise.apigee.com/v1/organizations/${org}/developers/ian.robinson27@nhs.net/apps/${service_base_path}" \
        --header "Authorization: Bearer ${access_token}" \
        -X DELETE

        existing_app_id="null" # Marks the API to be re-created below
    fi
  fi

  if [[ "$existing_app_id" == "null" ]]; then
    echo "Creating new Apigee app"
    api_body="{
          \"apiProducts\": [
              \"healthcare-worker-api--${apim_environment}--${service_base_path}--app-level3\"
          ],
          \"attributes\": [
              {
                  \"name\": \"DisplayName\",
                  \"value\": \"${service_base_path}\"
              },
              {
                  \"name\": \"environment\",
                  \"value\": \"${apim_environment}\"
              },
              {
                  \"name\": \"jwks-resource-url\",
                  \"value\": \"https://raw.githubusercontent.com/NHSDigital/identity-service-jwks/refs/heads/main/jwks/internal-dev/5eef95c7-031c-4d7b-ab58-1fee6e91a915.json\"
              }
          ],
          \"name\": \"${service_base_path}\",
          \"scopes\": [],
          \"status\": \"approved\"
      }"

    # It appears that apigee's API has a limitation which doesn't allow us to register apps to a team through the API:
    # see https://apidocs.apigee.com/apis?search=apps and https://apidocs.apigee.com/docs/developer-apps/1/overview
    # The choice of user shouldn't make any difference since we don't need to modify it, but it's obviously not ideal
    # to link to an individual.

    echo "Sending to https://api.enterprise.apigee.com/v1/organizations/${org}/developers/ian.robinson27@nhs.net/apps"
    app_details=$(curl --location "https://api.enterprise.apigee.com/v1/organizations/${org}/developers/ian.robinson27@nhs.net/apps" \
      --header "Authorization: Bearer ${access_token}" \
      --header 'Content-Type: application/json' \
      --data "$api_body")

    echo "App creation request sent:"
    echo "$app_details"
  fi

  env_app_client_id=$(echo "$app_details" | jq -r ".credentials[0].consumerKey")
  echo "Client id = ${env_app_client_id}"
fi
