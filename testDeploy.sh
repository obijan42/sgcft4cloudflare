#!/usr/bin/env bash
#clear
#export AWS_DEFAULT_PROFILE=yourprofilehere

stackname=SecGroupCloudflare
filename=${stackname}.template


echo "Running stack : $stackname ... "
# Whoami
aws sts get-caller-identity --query Arn  --output text|| { echo "FATAL: Login failed"; exit 1; }

# Test template
aws cloudformation validate-template --template-body file://${filename} --output table || { echo "FATAL: Validation failed"; exit 1; }


#Delete existing
# aws cloudformation list-stacks  --stack-status-filter  CREATE_IN_PROGRESS  CREATE_FAILED CREATE_COMPLETE ROLLBACK_IN_PROGRESS ROLLBACK_COMPLETE
echo "Starting delete:"
aws cloudformation delete-stack --stack-name  $stackname
echo "Waiting for deletion to be completed..."
time aws cloudformation wait stack-delete-complete --stack-name  $stackname

echo "Creating new:"

# Cheat by grabbing the first vpc that comes up
myvpc=$(aws ec2 describe-vpcs --query Vpcs[0].VpcId --output text)

aws cloudformation create-stack --stack-name  $stackname  --template-body file://${filename}  \
  --timeout-in-minutes 5  --output text \
  --parameters   ParameterKey=vpc,ParameterValue=$myvpc \
  || { echo "FATAL: Create failed"; exit 1; }

echo "Waiting for create to be completed..."
time aws cloudformation wait stack-create-complete --stack-name  $stackname
echo "Done."

aws cloudformation describe-stacks --stack-name  $stackname  --query Stacks[0].[StackName,StackStatus,Parameters[*].ParameterValue]  --output text
aws cloudformation list-stack-resources --stack-name  $stackname --query StackResourceSummaries[].[ResourceType,LogicalResourceId,PhysicalResourceId] --output table
