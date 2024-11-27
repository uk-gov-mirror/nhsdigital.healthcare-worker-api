packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.8"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

source "amazon-ebs" "hcw-nft" {
  ami_name      = "hcw-nft"
  instance_type = "t2.micro"
  region        = "eu-west-2"

  vpc_id = "vpc-035b2e3600afb9273"
  ssh_interface = "public_ip"
  associate_public_ip_address = true

  subnet_filter {
    filters = {
      "state": "available"
    }
    random = true
  }

  source_ami_filter {
    filters = {
      name                = "ubuntu/images/*ubuntu-noble-24.04-amd64-server*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]
  }
  ssh_username = "ubuntu"
}

build {
  name = "hcw-nft-2024-11-15"
  sources = [
    "source.amazon-ebs.hcw-nft"
  ]

  provisioner "file" {
    source = "../nft"
    destination = "/home/ubuntu/"
  }

  # Copying the integration tests because we're making use of their utils package
  provisioner "file" {
    source = "../integration_tests/utils"
    destination = "/home/ubuntu/nft/"
  }

  provisioner "shell" {
    inline = [
      "bash /home/ubuntu/nft/ec2/locust_setup.bash"
    ]
  }

  post-processor "manifest" {
    output = "ec2/manifest.json"
    strip_path = true
  }
}
