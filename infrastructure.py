from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os
from s3_bucket import create_bucket, delete_bucket
from AWS_Batch import *
import time
from AWS_Lambda import *
from AWS_API_GATEWAY import *
from bson import ObjectId

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)

# function to create the infrastructure
def create_infrastructure(username):
    # username = 
    # username = input("Enter the client name (No special character is allowed): ").replace(" ", "").lower()
    # print(username)
    # return
    
    if not username:
        print("Client name cannot be empty. Exiting...")
        return
    
    try:        
        # create database
        database = username
        db = client[database]
        print(f"{database} database created successfully")

        # create configuration collection
        print("\nCreating configuration collection...")
        create_configuration(database)

        # create collections
        print("\nCreating collections...")
        create_collections(database)
     
        try:
            # create S3 bucket
            print("\nCreating S3 bucket...")
            s3_bucket = create_s3_bucket(database)
            # print(s3_bucket)
            if not s3_bucket:
                print("Failed to create S3 bucket. Exiting...")
                print("\n\n**** Deleting the infrastructure... ****")
                print("Deleting the database...")
                delete_mongo_database(database)
                return
            
            try:
                # AWS Batch configuration
                print("\nCreating AWS Batch configuration...")
                batch = aws_batch_configuration(database)
                if not batch:
                    print("Deleting the s3 bucket...")
                    delete_bucket(f"{database}-bucket")
                    print("Deleting the database...")
                    delete_mongo_database(database)
                    return
                
                try:
                    # Lambda configuration
                    print("\nLambda configuration...")
                    lambda_function = lambda_configuration(database)
                    if not lambda_function:
                        print("Deleting the s3 bucket...")
                        delete_bucket(f"{database}-bucket")
                        print("Deleting the database...")
                        delete_mongo_database(database)
                        return
                    
                    try:
                        # API Gateway Configuration
                        print("\nAPI Gateway Configuration...")
                        api = api_gateway_configuration(database)
                        if not api:
                            print("Deleting the s3 bucket...")
                            delete_bucket(f"{database}-bucket")
                            print("Deleting the database...")
                            delete_mongo_database(database)
                            return
                        
                    except Exception as e:
                        print(f"An error occured: {e}")
                        print("\n\n**** Deleting the infrastructure... ****")
                        print("Deleting the Lambda Function...")
                        delete_lambda_function(f"{database}_shopify_lambda_function")
                        print("Deleting the IAM role...")
                        delete_iam_role(f"{database}_shopify_role")
                        print("Deleting the job definition...")
                        delete_job_definition(f"{database}_shopify_job_definition")
                        print("Deleting the job queue...")
                        delete_job_queue(f"{database}_shopify_job_queue")
                        print("Deleting the compute environment...")
                        delete_compute_environment(f"{database}_shopify_compute_environment")
                        print("Deleting the s3 bucket...")
                        delete_bucket(f"{database}-bucket")
                        print("Deleting the database...")
                        delete_mongo_database(database)
                        return

                except Exception as e:
                    print(f"An error occurred: {e}")
                    print("\n\n**** Deleting the infrastructure... ****")
                    print("Deleting the IAM role...")
                    delete_iam_role(f"{database}_shopify_role")
                    print("Deleting the job definition...")
                    delete_job_definition(f"{database}_shopify_job_definition")
                    print("Deleting the job queue...")
                    delete_job_queue(f"{database}_shopify_job_queue")
                    print("Deleting the compute environment...")
                    delete_compute_environment(f"{database}_shopify_compute_environment")
                    print("Deleting the s3 bucket...")
                    delete_bucket(f"{database}-bucket")
                    print("Deleting the database...")
                    delete_mongo_database(database)
                    return

            except Exception as e:
                print(f"An error occurred: {e}")
                print("\n\n**** Deleting the infrastructure... ****")
                print("Deleting the s3 bucket...")
                delete_bucket(f"{database}-bucket")
                print("Deleting the database...")
                delete_mongo_database(database)
                return
    
        except Exception as e:
            print(f"An error occurred: {e}")
            print("\n\n**** Deleting the infrastructure... ****")
            print("Deleting the database...")
            delete_mongo_database(database)
            return
        
        print("\n\n**** Infrastructure created successfully ****")
        create_client_DB_maping(username, database)
    except ConnectionFailure:
        print("Failed to connect to MongoDB server. Please ensure MongoDB is running")
    except Exception as e:
        print(f"An error occurred: {e}")


# function to insert the client name and client database name in Mapping Database
def create_client_DB_maping(clientName, dbName):
    try:
        client_db_mapping = client['clientInfo']
        collection=client_db_mapping['clientDbMapping']
        try:
            collection.update_one(
                {"_id": ObjectId("67ca83c559e92fccc46a0604")},
                {
                    "$set": {
                        f'{clientName}': f'{dbName}'
                    }
                }
            )
            print("\nUpdated the client name and database on 'ClientInfo' database")
        except Exception as e:
            print(f"\nFailed to update the client name and database on 'ClientInfo' database: {e}")
    except ConnectionError:
        print("\nFailed to connect to MongoDB server. Please ensure MongoDB is running")
    except Exception as e:
        print(f"\nAn error occured: {e}")


# function to create configuration collection
def create_configuration(database_name):
    try:
        database = client[database_name]

        # create configuration collection
        configuration_collection = database[f'{database.name}_Configuration']
        print("\nConfiguration Collection created successfully")

        configuration_collection.insert_many([
            {
                "DATABASE_NAME": f"{database.name}",
                "SHOPIFY_PRODUCT_COLLECTION": f"{database.name}_Shopify_Product",
                "SHOPIFY_LOGS_COLLECTION": f"{database.name}_Shopify_Logs",
                "SHOPIFY_COMPUTE_ENVIRONMENT_NAME": f"{database.name}_shopify_compute_environment",
                "SHOPIFY_JOB_QUEUE_NAME": f"{database.name}_shopify_job_queue",
                "SHOPIFY_JOB_DEFINITION_NAME": f"{database.name}_shopify_job_definition",
                "SHOPIFY_JOB_NAME": f"{database.name}_shopify_job",
                "SHOPIFY_LAMBDA_FUNCTION_NAME": f"{database.name}_shopify_lambda_function",
                "SHOPIFY_LAMBDA_ROLE_NAME": f"{database.name}_shopify_role",
                "S3_BUCKET_NAME": f"{database.name}-bucket",
                "SHOPIFY_API_NAME": f"{database.name}_shopify_api",
                "AWS_REGION": "ap-south-1",
                "SHOPIFY_STORE_NAME": "",
                "SHOPIFY_API_KEY": "",
                "SHOPIFY_ACCESS_TOKEN": ""
            }
        ])
        print("Configuration inserted successfully")
    except ConnectionFailure:
        print("Failed to connect to MongoDB server. Please ensure MongoDB is running")
    except Exception as e:
        print(f"An error occurred: {e}")


# function to create collections
def create_collections(database):
    db = client[database]
    collection = db[f'{db.name}_Configuration']
    document = collection.find_one()
    # create collection for Shopify products
    collection_shopify_product = db[document['SHOPIFY_PRODUCT_COLLECTION']]
    print("\n'SHOPIFY_PRODUCT_COLLECTION' collection created successfully")
    collection_shopify_product.insert_one({"name": "test"})
    print("Dummy document inserted to create the collection.")
    try:
        collection_shopify_product.delete_one({"name": "test"})
        print("Dummy document deleted successfully from 'SHOPIFY_PRODUCT_COLLECTION'")
    except Exception as e:
        print(f"Failed to delete dummy document from 'SHOPIFY_PRODUCT_COLLECTION': {e}")

    # create collection for Shopify logs
    collection_shopify_logs = db[document['SHOPIFY_LOGS_COLLECTION']]
    print("\n'SHOPIFY_LOGS_COLLECTION' collection created successfully")
    collection_shopify_logs.insert_one({"name": "test"})
    print("Dummy document inserted to create the collection.")

    try:
        collection_shopify_logs.delete_one({"name": "test"})
        print("Dummy document deleted successfully from 'SHOPIFY_LOGS_COLLECTION'")
    except Exception as e:
        print(f"Failed to delete dummy document from 'SHOPIFY_LOGS_COLLECTION': {e}")


# function to create S3 Bucket
def create_s3_bucket(database):
    db = client[database]
    collection = db[f'{db.name}_Configuration']
    document = collection.find_one()
    s3_bucket = create_bucket(document['S3_BUCKET_NAME'], document['AWS_REGION'])
    return s3_bucket


# function to configure AWS Batch
def aws_batch_configuration(database):
    db = client[database]
    collection = db[f'{db.name}_Configuration']
    document = collection.find_one()
    print("\nCreating compute environment...")
    status = create_compute_environment(document['SHOPIFY_COMPUTE_ENVIRONMENT_NAME'])
    # print("Status:", status)
    if status['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Compute environment created successfully")
    else:
        print("Failed to create compute environment. Exiting...")
        print("\n\n**** Deleting the infrastructure... ****")
        return False
    time.sleep(20)

    print("\nCreating job queue...")
    status = create_job_queue(document['SHOPIFY_JOB_QUEUE_NAME'], document['SHOPIFY_COMPUTE_ENVIRONMENT_NAME'])
    # print("Status:", status)
    if status['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Job queue created successfully")
    else:
        print("Failed to create job queue. Exiting...")
        print("\n\n**** Deleting the infrastructure... ****")
        print("Deleting the compute environment...")
        delete_compute_environment = delete_compute_environment(document['SHOPIFY_COMPUTE_ENVIRONMENT_NAME'])
        return False
    time.sleep(20)

    print("\nCreating job definition...")
    status = create_job_definition(document['SHOPIFY_JOB_DEFINITION_NAME'])
    # print("Status:", status)
    if status['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Job definition created successfully")
    else:
        print("Failed to create job definition. Exiting...")
        print("\n\n**** Deleting the infrastructure... ****")
        print("Deleting the job queue...")
        delete_job_queue = delete_job_queue(document['SHOPIFY_JOB_QUEUE_NAME'])
        print("Deleting the compute environment...")
        delete_compute_environment = delete_compute_environment(document['SHOPIFY_COMPUTE_ENVIRONMENT_NAME'])
        return False
    
    return True


# fucntion to configure lambda function
def lambda_configuration(database):
    db = client[database]
    collection = db[f'{db.name}_Configuration']
    document = collection.find_one()
    print("\nCreating IAM role for Lambda function...")
    iam_status = create_lambda_execution_role(document['SHOPIFY_LAMBDA_ROLE_NAME'])
    # print("Status:", iam_status)
    print("IAM role created successfully")
    time.sleep(5)
    try: 
        print("\nCreating Lambda function...")
        status = create_lambda_function(
            function_name=document['SHOPIFY_LAMBDA_FUNCTION_NAME'], 
            role_arn=f"arn:aws:iam::654654551634:role/{document['SHOPIFY_LAMBDA_ROLE_NAME']}",
            job_queue=document['SHOPIFY_JOB_QUEUE_NAME'],
            job_definition=document['SHOPIFY_JOB_DEFINITION_NAME'],
            job_name=document['SHOPIFY_JOB_NAME']
        )
        print("Status:", status)
        try:
            collection.update_one(
                {"DATABASE_NAME": f"{db.name}"},
                {"$set": {'SHOPIFY_LAMBDA_ARN': status}}
            )
            print("Lambda ARN successfully saved to configuration collection")
        except Exception as e:
            print(f"Error occured while saving Lambda ARN into configuration collection: {str(e)}")
        print("Lambda function created successfully")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Failed to create Lambda function. Exiting...")
        print("\n\n**** Deleting the infrastructure... ****")
        print("Deleting the IAM role...")
        delete_iam_role(document['SHOPIFY_LAMBDA_ROLE_NAME'])
        print("Deleting the job definition...")
        delete_job_definition(document['SHOPIFY_JOB_DEFINITION_NAME'])
        print("Deleting the job queue...")
        delete_job_queue(document['SHOPIFY_JOB_QUEUE_NAME'])
        print("Deleting the compute environment...")
        delete_compute_environment(document['SHOPIFY_COMPUTE_ENVIRONMENT_NAME'])
        return False


# function to configure API Gateway
def api_gateway_configuration(database):
    db = client[database]
    collection = db[f'{db.name}_Configuration']
    document = collection.find_one()
    print("\nCreating API Gateway...")
    try:
        deployment_response, api_id, api_url = create_api_gateway(document['SHOPIFY_API_NAME'], document['SHOPIFY_LAMBDA_ARN'])
        print("API Gateway Created and Deployed:", deployment_response)
        print(f"API Gateway Endpoint: {api_url}")
        try:
            collection.update_many(
                {"DATABASE_NAME": f"{db.name}"},
                {
                    '$set': {
                        'SHOPIFY_API_ID': api_id,
                        'SHOPIFY_API_GATEWAY_ENDPOINT': api_url
                    }
                }
            )

            print("API ID and API Endpoint are successfully saved to configuration collection")
        
        except Exception as e:
            print(f"Error occured while saving api id and epi endpoint in configuration collection: {e}")
        
        return True
    
    except Exception as e:
        print(f"An error occured: {e}")
        print("Failed to create API Gateway. Exiting...")
        print("\n\n**** Deleting the infrastructure... ****")
        print("Deleting the Lambda Function...")
        delete_lambda_function(document['SHOPIFY_LAMBDA_FUNCTION_NAME'])
        print("Deleting the IAM role...")
        delete_iam_role(document['SHOPIFY_LAMBDA_ROLE_NAME'])
        print("Deleting the job definition...")
        delete_job_definition(document['SHOPIFY_JOB_DEFINITION_NAME'])
        print("Deleting the job queue...")
        delete_job_queue(document['SHOPIFY_JOB_QUEUE_NAME'])
        print("Deleting the compute environment...")
        delete_compute_environment(document['SHOPIFY_COMPUTE_ENVIRONMENT_NAME'])
        return False


# function to delete the mongo database
def delete_mongo_database(db_name):
    try:
        if db_name not in client.list_database_names():
            print(f"{db_name} database does not exist. Exiting...")
            return
        client.drop_database(db_name)
        print(f"{db_name} database deleted successfully")
    except ConnectionFailure:
        print("Failed to connect to MongoDB server. Please ensure MongoDB is running")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    create_infrastructure()
    # create_client_DB_maping("hello", "hello")
