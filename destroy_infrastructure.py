from dotenv import load_dotenv
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from AWS_API_GATEWAY import delete_api_gateway
from AWS_Lambda import delete_lambda_function, delete_iam_role
from AWS_Batch import delete_job_definition, delete_job_queue, delete_compute_environment
from s3_bucket import delete_bucket
from delete_client import delete_client


load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)


def delete_infrastructure():
    database_name = input("Enter the client name: ")

    if not database_name:
        print("Client name cannot be empty. Exiting...")
        return

    try:
        db = client[database_name]
        collection = db[f"{database_name}_Configuration"]
        configuration = collection.find_one()

        print("\n**** Deleting the Complete Infrastructure ****")
        # Delete the API Gateway
        print("\nDeleting API Gateway...")
        delete_api_gateway(configuration["SHOPIFY_API_ID"])

        # Delete the Lambda function
        print("\nDeleting Shopify Lambda Function...")
        delete_lambda_function(configuration["SHOPIFY_LAMBDA_FUNCTION_NAME"])

        # Delete the IAM role
        print("\nDeleting Shopify Lambda IAM Role...")
        delete_iam_role(configuration["SHOPIFY_LAMBDA_ROLE_NAME"])

        # Delete the job definition
        print("\nDeleting Shopify Job Definition...")
        delete_job_definition(configuration["SHOPIFY_JOB_DEFINITION_NAME"])

        # Delete the job queue
        print("\nDeleting Shopify Job Queue...")
        delete_job_queue(configuration["SHOPIFY_JOB_QUEUE_NAME"])

        # Delete the compute environment
        print("\nDeleting Shopify Compute Environment...")
        delete_compute_environment(configuration["SHOPIFY_COMPUTE_ENVIRONMENT_NAME"])
        
        # Delete the S3 bucket
        print("\nDeleting S3 Bucket...")
        delete_bucket(configuration["S3_BUCKET_NAME"])

        # Delete the Data of Client from Mapping DB
        print("\nDeleting the client information from mapping database...")
        delete_client(configuration["DATABASE_NAME"])
        
        # Delete the MongoDB database
        print("\nDeleting Database...")
        client.drop_database(configuration["DATABASE_NAME"])
        
        # Close the MongoDB connection
        client.close()
        
        print("\n**** Infrastructure deleted successfully ****")

    except ConnectionFailure:
        print("\nFailed to connect to MongoDB server. Please ensure MongoDB is running")
    except Exception as e:
        print(f"An error occured: {e}")


if __name__ == '__main__':
    delete_infrastructure()
