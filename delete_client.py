from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)

# function to delete the client details from the Mapping Database
def delete_client(client_name):  
    try:
        client_db_mapping = client['clientInfo']
        collection = client_db_mapping['clientDbMapping']
        try:
            collection.update_one(
                {"_id": ObjectId("67ca83c559e92fccc46a0604")},
                {
                    "$unset": {
                        f'{client_name}': f'{client_name}'
                    }
                }
            )
            print("\nDelete the client name and database name from the 'ClientInfo' database")
        except Exception as e:
            print(f"\nFailed to delete the client name and database name from 'ClientInfo' database: {e}")
    except ConnectionFailure:
        print("\nFailed to connect to MongoDB server. Please ensure MongoDB is running")
    except Exception as e:
        print(f"\nAn error occured: {e}")
