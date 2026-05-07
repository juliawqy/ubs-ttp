terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "ubs-ttp-tfstate-production"
    key            = "global/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "ubs-ttp-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

module "networking" {
  source = "../../modules/networking"
  env    = var.env
}

module "eks" {
  source     = "../../modules/eks"
  env        = var.env
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
}

module "rds" {
  source     = "../../modules/rds"
  env        = var.env
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
}

module "cognito" {
  source = "../../modules/cognito"
  env    = var.env
}

module "s3" {
  source = "../../modules/s3"
  env    = var.env
}

module "sqs_sns" {
  source = "../../modules/sqs-sns"
  env    = var.env
}

module "elasticache" {
  source     = "../../modules/elasticache"
  env        = var.env
  subnet_ids = module.networking.private_subnet_ids
}

module "cloudfront" {
  source = "../../modules/cloudfront"
  env    = var.env
}
