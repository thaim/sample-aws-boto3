terraform {
  required_version = "~> 1.5"
  required_providers {
    aws = {
      version = "~> 5.30.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
  default_tags {
    tags = {
      manager = "terraform"
      repo    = "github.com/thaim/sample-aws-boto3/ecs-volume"
    }
  }
}
