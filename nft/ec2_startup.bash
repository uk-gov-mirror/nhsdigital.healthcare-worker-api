#!/bin/bash
# This script executes when the ec2 instance starts. It triggers the actual NFT tests, copies the resulting CSV files
# to S3, and then shuts down the EC2 instance to save money.

# Wait a bit to make sure that the correct iam roles have been assigned to the instance
sleep 10
PATH=$PATH:/home/ubuntu/.local/bin

cd /home/ubuntu/nft || exit 1
poetry install

export CLIENT_ID="KG8XEhXyL0iHP3wN8hKM6KVgDInd2DX0"
if [[ "ft" == "ft" ]]; then
  url=https://internal-dev.api.service.nhs.uk/healthcare-worker
else
  url=https://internal-dev.api.service.nhs.uk/healthcare-worker/"ft"
fi
poetry run locust -f src/nft.py -H "${url}" -u "20" -r "0.1" -t "10m" --csv nft --headless --processes "4"

now=$(date +%FT%H:%M)
mkdir "$now"
cp ./*.csv "${now}/"
aws s3 sync "$now" "s3://ft-nft-test-results/${now}"

# Shutdown the EC2 instance now that the test is complete
#sudo shutdown now -h
