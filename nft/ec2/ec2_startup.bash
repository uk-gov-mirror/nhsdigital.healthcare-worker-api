#!/bin/bash
# This script executes when the ec2 instance starts. It triggers the actual NFT tests, copies the resulting CSV files
# to S3, and then shuts down the EC2 instance to save money.

# Wait a bit to make sure that the correct iam roles have been assigned to the instance
sleep 10
PATH=$PATH:/home/ubuntu/.local/bin

cd /home/ubuntu/nft || exit 1
poetry install

export CLIENT_ID="${CLIENT_ID}"
if [[ "${ENV}" == "ft" ]]; then
  url=https://internal-dev.api.service.nhs.uk/healthcare-worker
else
  url=https://internal-dev.api.service.nhs.uk/healthcare-worker/"${ENV}"
fi
poetry run locust -f src/nft.py -H "${url}" -u "${USERS}" -r "${RAMP_UP}" -t "${DURATION}" --csv nft --headless --processes "${WORKER_COUNT}"

now=$(date +%FT%H:%M)
mkdir "$now"
cp ./*.csv "${now}/"
aws s3 sync "$now" "s3://ft-nft-test-results/${now}"

# Shutdown the EC2 instance now that the test is complete
sudo shutdown now -h
