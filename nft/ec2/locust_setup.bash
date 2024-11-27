#!/bin/bash

cd /home/ubuntu/nft || exit 1

sudo apt update
sudo apt -y install pipx

pipx install poetry
pipx ensurepath
export PATH=$PATH:/home/ubuntu/.local/bin

sudo snap install aws-cli --classic
