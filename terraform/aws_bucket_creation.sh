#!/bin/bash

set -ex

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="aero-bound-tfstate-${ACCOUNT_ID}"

# 1. Create S3 bucket
aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region us-east-2 \
    --create-bucket-configuration LocationConstraint=us-east-2

# 2. Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

# 3. Set bucket policy
aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Effect\": \"Allow\",
                \"Principal\": { \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\" },
                \"Action\": [\"s3:ListBucket\"],
                \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}\"
            },
            {
                \"Effect\": \"Allow\",
                \"Principal\": { \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\" },
                \"Action\": [\"s3:GetObject\", \"s3:PutObject\", \"s3:DeleteObject\"],
                \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}/*\"
            }
        ]
    }"

echo "✅ Bucket $BUCKET_NAME created with versioning and policy configured"