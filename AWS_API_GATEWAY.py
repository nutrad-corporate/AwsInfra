import boto3

# Initialize the Boto3 clients
lambda_client = boto3.client('lambda')
apigateway_client = boto3.client('apigateway')
iam_client = boto3.client('iam')

def create_api_gateway(api_name, lambda_arn):
    try:
        response = apigateway_client.create_rest_api(
            name=api_name,
            description='API Gateway for lambda function',
            version='1.0',
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )

        api_id = response['id']
        resources = apigateway_client.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']

        # Create GET method on the root path
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod='GET',
            authorizationType='NONE'
        )

        # Connect the GET method to the Lambda function
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod='GET',
            integrationHttpMethod='POST',
            type='AWS_PROXY',
            uri=f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )

        # Create method response for 200 status code
        apigateway_client.put_method_response(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod='GET',
            statusCode='200',
            responseModels={
                'application/json': 'Empty'
            }
        )

        # Create integration response
        apigateway_client.put_integration_response(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod='GET',
            statusCode='200',
            selectionPattern=''
        )

        # Deploy the API Gateway
        deployment_response = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )

        # Construct the source ARN for the Lambda Permission
        source_arn = f'arn:aws:execute-api:ap-south-1:654654551634:{api_id}/*/GET/'

        # Grant API Gateway permission to invoke Lambda function
        try:
            lambda_client.add_permission(
                FunctionName=lambda_arn,
                StatementId=f'apigateway-invoke-{api_id}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )

            print("Permission added successfully for API Gateway to invoke Lambda.")

        except lambda_client.exceptions.ResourceConflictException:
            # If permission already exists, skip and continue
            print("Permission already exists. Skipping...")
        
        # Get the API endpoint URL
        api_url = f"https://{api_id}.execute-api.ap-south-1.amazonaws.com/prod"


        return deployment_response, api_id, api_url
    
    except Exception as e:
        print(f"Error occured while creating the API Gateway: {str(e)}")


def delete_api_gateway(api_id):
    try:
        apigateway_client.delete_rest_api(
            restApiId=api_id
        )
        print(f"API Gateway {api_id} and its associated resources have been deleted successfully.")
    
    except Exception as e:
        print(f"Error occurred while deleting the API Gateway: {str(e)}")
