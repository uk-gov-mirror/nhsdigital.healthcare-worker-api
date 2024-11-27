#!/bin/bash

source .nft.env

INSTANCE_PROFILE_NAME="ft-nft-instance-profile"

artifact_prefix="eu-west-2:"
last_build_id=$(jq -r ".last_run_uuid" ec2/manifest.json)
artifact_id=$(jq -r ".builds[] | select(.packer_run_uuid==\"${last_build_id}\").artifact_id" ec2/manifest.json)
AMI_ID=${artifact_id#$artifact_prefix}

# We need to create a temporary version of the launch script with variables from .nft.env populated. This is so that
# we don't need to build a fresh AMI for every different test config.
cp ./ec2/ec2_startup.bash ec2_startup.bash
sed -i "" "s/\${ENV}/${ENV}/g" ec2_startup.bash
sed -i "" "s/\${CLIENT_ID}/${CLIENT_ID}/g" ec2_startup.bash
sed -i "" "s/\${USERS}/${USERS}/g" ec2_startup.bash
sed -i "" "s/\${RAMP_UP}/${RAMP_UP}/g" ec2_startup.bash
sed -i "" "s/\${DURATION}/${DURATION}/g" ec2_startup.bash
sed -i "" "s/\${WORKER_COUNT}/${WORKER_COUNT}/g" ec2_startup.bash

echo "Launching EC2 Instance"
INSTANCE_ID=$(aws ec2 run-instances --image-id "${AMI_ID}" --count 1 --instance-type "${INSTANCE_TYPE}" --security-group-ids "${SECURITY_GROUP_ID}" --subnet-id "${SUBNET_ID}" --query 'Instances[0].InstanceId' --output text --user-data file://ec2_startup.bash --associate-public-ip-address --key-name dev-1)
aws ec2 wait instance-running --instance-ids "${INSTANCE_ID}"
aws ec2 associate-iam-instance-profile --instance-id "${INSTANCE_ID}" --iam-instance-profile Name="${INSTANCE_PROFILE_NAME}"
echo "EC2 Instance Running at $(date)}"

rm ec2_startup.bash


