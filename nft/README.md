# HCW API NFT Framework

This project contains NFT tests for running against a deployed instance of the HCW API.

NFT tests are run from an EC2 instance in AWS. It's important to ensure that these tests are reliable and repeatable and
so we want to reduce the number of manual steps required. For this reason we build the base image as an AWS AMI and then
create new EC2 instances for each NFT test. This setup allows us to only have EC2 instances running for the duration of
the NFT test, keeping costs to a minimum.

We aren't currently running any performance tests as part of our automated deployment, and so we rely on it being
manually triggered as required. This readme contains the steps necessary for running them. This includes the ability
to rebuild the runner AMI, although this is normally not required.

The test runner is built and executed from the dev AWS account, in a VPC with access to the internet. Our requests are
going from the dedicated AWS VPC to the APIM Gateway (hosted in Azure), so the NFT results are not affecting by being
started from the same account. Running from the dev account means that we don't risk any limits affecting PTL environments.

## Test config options

Every test run is different, with different loads and environments being tested. This means that we often need to change
the run config to suit our needs. The `.nft.env` file contains all the properties that we might want to change between tests.
This includes the environment to test against, and how long the test should last.

## Launching a test run

Once you've ensured that the `.nft.env` file contains the correct settings you can trigger the test run with the command
`bash launch_nft_test.bash`. This uses the latest built AMI to run the defined integration tests, with an EC2 instance
launched for the purpose and then automatically shutdown once complete.

This runner does not affect the target environment in any way. You may want to make some changes before starting these
tests (e.g. setting some provisioned capacity on the lambda), but that's left as a manual activity.

The following is a common error caused by your AWS credentials being out of date, make sure that you've updated the
relevant environment variables and try the bash command again.

```bash
An error occurred (RequestExpired) when calling the RunInstances operation: Request has expired.
```

There isn't much in the way of ongoing feedback while the test is running, but there are a few things you can double
check to make sure they're as expected. Firstly, after launching an NFT run there should be a new instance listed
on the EC2 console. This instance will be running for only slightly longer than the test duration you specified.

If the EC2 instance is still active you can see the latest logs by connecting to the instance. You can do this through
the EC2 Instance Connect functionality in the AWS console. Once connected, check the logs at `/var/log/cloud-init-output.log`
to see the latest logs. This can be particularly useful to make sure that the tests have started, but there isn't much
in the way of logging during the test.

If you are facing an issue you need to debug, you might want to disable the automatic shutdown at the end of `ec2_startup.bash`
so that you have the time to connect to the instance and view the logs.

## Test Results

The test results are published to the `ft-nft-test-results` S3 bucket under a folder with the completion date and time.
Inside the folder are four csvs with the test result summary.

You can also view the EC2 metrics for the instance, even for some time once it's been terminated. This can be useful if
you suspect that the test runner itself might be a limitation. For example, particularly high CPU utilisation might suggest
that you need to improve the runner spec.

Once you have the test results, create a new child page under [HCW NFT Results](https://nhsd-confluence.digital.nhs.uk/pages/viewpage.action?spaceKey=CIS&title=HCW+NFT+Results)
with the relevant details.

## Test definition

The actual tests are defined in `src/nft.py`. This is what we want to modify with new app functionality. It also defines
the wait time between requests, which might be something that we want to change to better represent production loads.

## Building the AMI

To build the AMI you must have the [Packer CLI](https://developer.hashicorp.com/packer/tutorials/docker-get-started/get-started-install-cli)
installed, the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and
authenticated into the management account.

AMI names need to be unique, and so you will probably need to change the `name` field in the `build` block in `locust.pkr.hcl`
before performing the build. If you do this, consider removing the existing AMI once complete to save costs. To delete
an AMI navigate to it in the AWS EC2 console, select the "Actions" dropdown and select "Dereigster AMI". Make sure to
also delete the associated EBS snapshot.

To build, run the following commands from the current directory:

```bash
packer init .
packer build .
```

Once complete check the output file `ec2/manifest.json` which will include the newly generated ami id. The new AMI will be
automatically picked up from this file when you trigger the next NFT test run.
