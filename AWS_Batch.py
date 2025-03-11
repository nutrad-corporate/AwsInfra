import boto3
from botocore.exceptions import ClientError
import time

# Initialize AWS Clients
batch_client = boto3.client('batch')

def create_compute_environment(compute_environment_name):
    response = batch_client.create_compute_environment(
        computeEnvironmentName=compute_environment_name,
        type='MANAGED',
        state='ENABLED',
        computeResources={
            'type': 'FARGATE',
            'maxvCpus': 1,
            'subnets': [
                'subnet-099dbb7898fe530b3',
                'subnet-081e532a49f06d23f',
                'subnet-058335622aeac0d67'
            ],
            'securityGroupIds': [
                'sg-05965867a588003a0'
            ]
        }
    )

    return response

def create_job_queue(job_queue_name, compute_environment_name):
    response = batch_client.create_job_queue(
        jobQueueName=job_queue_name,
        priority=1,
        state='ENABLED',
        computeEnvironmentOrder=[
            {
                'order': 1,
                'computeEnvironment': compute_environment_name
            }
        ]
    )

    return response

def create_job_definition(job_definition_name):
    response = batch_client.register_job_definition(
        jobDefinitionName=job_definition_name,
        platformCapabilities=[
            'FARGATE'
        ],
        type='container',
        containerProperties={
            'image': '654654551634.dkr.ecr.ap-south-1.amazonaws.com/nutrad/shopify:latest',
            'command': [
                'python',
                'post_product.py'
            ],
            "executionRoleArn": "arn:aws:iam::654654551634:role/AWSBatchExecutionRole",
            "networkConfiguration": {
                "assignPublicIp": "ENABLED"
            },
            "resourceRequirements": [
                {
                    "value": "1.0",
                    "type": "VCPU"
                },
                {
                    "value": "2048",
                    "type": "MEMORY"
                }
            ]
        }
    )

    return response


def delete_compute_environment(compute_environment_name):
    try:
        update_response = batch_client.update_compute_environment(
            computeEnvironment=compute_environment_name,
            state='DISABLED'
        )
        time.sleep(10)
        if update_response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Compute environment disabled successfully")
            response = batch_client.delete_compute_environment(
                computeEnvironment=compute_environment_name
            )
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("Compute environment deleted successfully")
            else:
                print("Failed to delete compute environment. Exiting...")
                return False
        else:
            print("Failed to disable compute environment. Exiting...")
            return False
    except ClientError as e:
        print(f"An error occurred: {e}")
        return False

    return True

def check_job_queue_deletion(job_queue_name, max_attempts=8, attempt=1, wait_time=10):
    try:
        # Try to describe the job queue
        batch_client.describe_job_queues(jobQueues=[job_queue_name])
        if attempt >= max_attempts:
            print(f"Timeout: Job queue {job_queue_name} deletion taking longer than expected")
            return False
        
        print(f"Waiting for job queue deletion... Attempt {attempt}/{max_attempts}")
        time.sleep(wait_time)
        return check_job_queue_deletion(job_queue_name, max_attempts, attempt + 1, wait_time)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClientException' 'not found' in e.response['Error']['Message'].lower():
            print(f"Job queue {job_queue_name} has been successfully deleted")
            return True
        else:
            print(f"Unexpected error while checking job queue status: {e}")
            return False

def delete_job_queue(job_queue_name, max_wait_time=120):
    try:
        # Check if job queue exists before attempting to delete
        try:
            batch_client.describe_job_queues(jobQueues=[job_queue_name])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ClientException' and 'not found' in e.response['Error']['Message'].lower():
                print(f"Job queue {job_queue_name} does not exist")
                return True
            else:
                raise e
                
        # Step 1: Disable the job queue
        print(f"Disabling job queue: {job_queue_name}")
        update_response = batch_client.update_job_queue(
            jobQueue=job_queue_name,
            state='DISABLED'
        )
        
        if update_response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print(f"Failed to disable job queue. Status code: {update_response['ResponseMetadata']['HTTPStatusCode']}")
            return False
            
        print(f"Job queue disabled successfully. Waiting for disable to take effect...")
        time.sleep(10)
        
        # Step 2: Delete the job queue
        print(f"Initiating deletion of job queue: {job_queue_name}")
        delete_response = batch_client.delete_job_queue(
            jobQueue=job_queue_name
        )
        
        if delete_response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print(f"Failed to initiate job queue deletion. Status code: {delete_response['ResponseMetadata']['HTTPStatusCode']}")
            return False
            
        # Step 3: Calculate appropriate parameters for deletion check
        max_attempts = max(1, int(max_wait_time / 10))
        wait_time = min(10, max_wait_time)
        
        # Step 4: Wait for the deletion to complete
        return check_job_queue_deletion(job_queue_name, max_attempts, 1, wait_time)
        
    except ClientError as e:
        print(f"Error during job queue deletion process: {str(e)}")
        return False
    

# def delete_job_queue(job_queue_name):
#     try:
#         update_response = batch_client.update_job_queue(
#             jobQueue=job_queue_name,
#             state='DISABLED'
#         )
#         time.sleep(10)
#         if update_response['ResponseMetadata']['HTTPStatusCode'] == 200:
#             print("Job queue disabled successfully")
#             response = batch_client.delete_job_queue(
#                 jobQueue=job_queue_name
#             )
#             if response['ResponseMetadata']['HTTPStatusCode'] == 200:
#                 print("Job queue deletion initiated. Waiting for completion...")
#                 if check_job_queue_deletion(job_queue_name):
#                     print("Job queue deleted successfully")
#             else:
#                 print("Failed to delete job queue. Exiting...")
#                 return False
#         else:
#             print("Failed to disable job queue. Exiting...")
#             return False
#     except ClientError as e:
#         print(f"An error occurred: {e}")
#         return False

def delete_job_definition(job_definition_name):
    try:
        # List all revisions of the job definition
        paginator = batch_client.get_paginator('describe_job_definitions')
        job_definitions = []
        
        for page in paginator.paginate(jobDefinitionName=job_definition_name, status='ACTIVE'):
            job_definitions.extend(page['jobDefinitions'])

        if not job_definitions:
            print(f"No active job definitions found for {job_definition_name}")
            return True

        # Deregister all revisions
        success = True
        for job_def in job_definitions:
            full_job_def_name = f"{job_def['jobDefinitionName']}:{job_def['revision']}"
            try:
                response = batch_client.deregister_job_definition(
                    jobDefinition=full_job_def_name
                )
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    print(f"Deregistered job definition: {full_job_def_name}")
                else:
                    print(f"Failed to deregister job definition: {full_job_def_name}")
                    success = False
            except ClientError as e:
                print(f"Error deregistering {full_job_def_name}: {e}")
                success = False

        if success:
            print(f"All revisions of job definition '{job_definition_name}' have been deregistered")
        return success

    except ClientError as e:
        print(f"An error occurred: {e}")
        return False
