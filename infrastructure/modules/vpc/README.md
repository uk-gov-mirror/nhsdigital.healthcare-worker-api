# VPC Module

We need one VPC per environment, with the exception of PRs which are all included in the internal-dev VPC.
So this module is somewhere between the hcw-api module which deploys separately with each PR, and the mgmt module
which is only needed once per account.
