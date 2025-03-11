import boto3
from botocore.exceptions import ClientError
import re
import json

def is_valid_bucket_name(bucket_name):
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        print("Bucket name should be between 3 and 63 characters long")
        return False
    if not re.match(r'^[a-z0-9.-]+$', bucket_name):
        print("Bucket name should contain only lowercase letters, numbers, hyphens and periods")
        return False
    if bucket_name.startswith('.') or bucket_name.endswith('.') or bucket_name.startswith('-') or bucket_name.endswith('-'):
        print("Bucket name should not start or end with a period or hyphen")
        return False
    if '..' in bucket_name:
        print("Bucket name should not contain consecutive periods")
        return False
    return True
    

def create_bucket(bucket_name, region=None, allow_public_access=True, enable_acl=True, allow_object_read=True, set_default_object_acl=True):
    try:
        if not is_valid_bucket_name(bucket_name):
            print("Invalid bucket name. Exiting...")
            return False
            
        # Create the S3 client with the appropriate region
        if region is None:
            s3_client = boto3.client('s3')
            # For default region (ap-south-1), we don't provide LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
        
        print(f"Bucket '{bucket_name}' created successfully")
        
        # Disable Block Public Access if requested
        if allow_public_access:
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            print(f"Block Public Access settings disabled for bucket '{bucket_name}'")
        
        # Enable ACLs if requested (by setting the bucket owner preferred option to 'ObjectWriter')
        if enable_acl:
            s3_client.put_bucket_ownership_controls(
                Bucket=bucket_name,
                OwnershipControls={
                    'Rules': [
                        {
                            'ObjectOwnership': 'ObjectWriter'
                        }
                    ]
                }
            )
            print(f"ACLs enabled for bucket '{bucket_name}'")
            
        # Set bucket ACL to allow public read access if requested
        if allow_object_read:
            # First, ensure ACLs are enabled
            if not enable_acl:
                s3_client.put_bucket_ownership_controls(
                    Bucket=bucket_name,
                    OwnershipControls={
                        'Rules': [
                            {
                                'ObjectOwnership': 'ObjectWriter'
                            }
                        ]
                    }
                )
                print(f"ACLs automatically enabled to support object READ access for bucket '{bucket_name}'")
            
            # Set the ACL to public-read
            s3_client.put_bucket_acl(
                Bucket=bucket_name,
                ACL='public-read'
            )
            print(f"Public READ access granted for objects in bucket '{bucket_name}'")
        
        # Set default ACLs for new objects if requested
        if set_default_object_acl:
            # Create bucket policy that sets default ACLs for new objects
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AddPublicReadACLToAllObjects",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }

            # Convert the policy to JSON
            policy_json = json.dumps(bucket_policy)

            # Apply the policy to the bucket
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=policy_json
            )

            print(f"Default public-read ACL policy set for new objects in bucket '{bucket_name}'")

        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'BucketAlreadyOwnedByYou':
            print(f"Bucket '{bucket_name}' already exists and is owned by you")
            return True
        elif error_code == 'BucketAlreadyExists':
            print(f"Bucket '{bucket_name}' already exists but is owned by another account")
            return False
        else:
            print(f"An error occurred: {e}")
            return False

def delete_bucket(bucket_name):
    try:
        # delete all objects in the bucket
        s3_client = boto3.client('s3')
        objects = s3_client.list_objects(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        
        # delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"{bucket_name} deleted successfully")
        return True
    except ClientError as e:
        print(f"An error occurred: {e}")
        return False
