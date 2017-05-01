#!/bin/bash

export AWS_DEFAULT_PROFILE="infosec-prod-admin"
export AWS_DEFAULT_REGION="us-west-2"
aws cloudformation create-stack --stack-name sso-dashboard-prod --template-body file://cloudformation/us-west-2.yml --capabilities CAPABILITY_NAMED_IAM --parameters  ParameterKey=SSHKeyName,ParameterValue=akrug-keys ParameterKey=EnvType,ParameterValue=prod
export AWS_DEFAULT_REGION="us-east-1"

sleep 60

region="us-east-1"
credstash_key_id="`aws --region $region kms list-aliases --query "Aliases[?AliasName=='alias/credstash'].TargetKeyId | [0]" --output text`"
role_arn="`aws iam get-role --role-name SSO-Dashboard-Role --query Role.Arn --output text`"
constraints="EncryptionContextEquals={app=sso-dashboard}"

# Grant the sso-dashboard IAM role permissions to decrypt
aws kms create-grant --key-id $credstash_key_id --grantee-principal $role_arn --operations "Decrypt" --constraints $constraints --name sso-dashboard
