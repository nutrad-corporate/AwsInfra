import boto3
import json
import io
import zipfile
import time

# Initialize AWS clients
batch_client = boto3.client('batch')
lambda_client = boto3.client('lambda')
iam_client = boto3.client('iam')

def create_lambda_execution_role(role_name):
    """Create IAM role for Lambda with permissions to submit Batch jobs"""
    
    # Create the IAM role for Lambda
    try:
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description="Role for Lambda to trigger AWS Batch jobs"
        )
        
        role_arn = response['Role']['Arn']
        
        # Attach policy allowing Lambda to submit Batch jobs
        batch_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "batch:SubmitJob",
                        "batch:DescribeJobs",
                        "batch:TerminateJob"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        policy_name = f"{role_name}-policy"
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(batch_policy)
        )
        
        # Wait for IAM role to propagate
        print("Waiting for IAM role to propagate...")
        time.sleep(10)
        
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Role {role_name} already exists. Retrieving ARN...")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']


def create_lambda_function(function_name, role_arn, job_queue, job_definition, job_name):
    """Create Lambda function that triggers the Batch job"""
    
    # Create Lambda function code
    lambda_code = """
import boto3
import json
import os

def lambda_handler(event, context):
    batch_client = boto3.client('batch')

    # submit the Job to AWS Batch
    response = batch_client.submit_job(
        jobName=os.environ['JOB_NAME'],
        jobQueue=os.environ['JOB_QUEUE'],
        jobDefinition=os.environ['JOB_DEFINITION'],
        containerOverrides={
            "command": ["python", "post_product.py"]
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps(f'Job submitted successfully with Job ID: {response['jobId']}')
    }
"""
    
    # Create a zip file in memory instead of using a temporary file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as z:
        z.writestr('lambda_function.py', lambda_code)
    
    zip_buffer.seek(0)
    zip_bytes = zip_buffer.read()
    
    try:
        # Create the Lambda function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.13',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_bytes},
            Description='Lambda function to trigger AWS Batch job for shopify post product',
            Timeout=30,
            MemorySize=128,
            Environment={
                'Variables': {
                    'JOB_QUEUE': job_queue,
                    'JOB_DEFINITION': job_definition,
                    'JOB_NAME': job_name
                }
            }
        )
        return response['FunctionArn']
        
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Lambda function {function_name} already exists. Updating...")
        
        # Update the Lambda function code
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_bytes
        )
        
        # Update the Lambda function configuration
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Role=role_arn,
            Environment={
                'Variables': {
                    'JOB_QUEUE': job_queue,
                    'JOB_DEFINITION': job_definition,
                    'JOB_NAME': job_name
                }
            }
        )
        
        return response['FunctionArn']


def delete_lambda_function(function_name):
    """Delete the Lambda function"""
    
    try:
        response = lambda_client.delete_function(FunctionName=function_name)
        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            print(f"Lambda function {function_name} deleted successfully")
            return True
        else:
            print(f"Failed to delete Lambda function {function_name}. Exiting...")
            return False
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function {function_name} not found")
        return False


def delete_iam_role(role_name):
    """Delete the IAM role and policy"""
    
    try:
        # Detach and delete the policy
        policy_name = f"{role_name}-policy"
        iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        
        # Delete the role
        response = iam_client.delete_role(RoleName=role_name)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"IAM role {role_name} deleted successfully")
            return True
        else:
            print(f"Failed to delete IAM role {role_name}. Exiting...")
            return False
        
    except iam_client.exceptions.NoSuchEntityException:
        print(f"IAM role {role_name} not found")
        return False
