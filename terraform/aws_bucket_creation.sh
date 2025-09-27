#!/bin/bash

set -ex

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. Create S3 bucket
aws s3api create-bucket \
    --bucket aero-bound-ventures-terraform-state-bucket \
    --region us-east-2 \
    --create-bucket-configuration LocationConstraint=us-east-2

# 2. Enable versioning
aws s3api put-bucket-versioning \
    --bucket aero-bound-ventures-terraform-state-bucket \
    --policy "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
            {
                \"Effect\": \"Allow\",
                \"Principal\": { \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\" },
                \"Action\": [\"s3:ListBucket\"],
                \"Resource\": \"arn:aws:s3:::aero-bound-ventures-terraform-state-bucket\",
                \"Condition\": { \"StringEquals\": { \"s3:prefix\": \"prod/terraform.tfstate\" } }
            },
            {
                \"Effect\": \"Allow\",
                \"Principal\": { \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\" },
                \"Action\": [\"s3:GetObject\",\"s3:PutObject\"],
                \"Resource\": \"arn:aws:s3:::aero-bound-ventures-terraform-state-bucket/prod/terraform.tfstate\"
            },
            {
                \"Effect\": \"Allow\",
                \"Principal\": { \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\" },
                \"Action\": [\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\"],
                \"Resource\": \"arn:aws:s3:::aero-bound-ventures-terraform-state-bucket/prod/terraform.tfstate.tflock\"
            }
            ]
        }"