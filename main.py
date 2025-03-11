from fastapi import FastAPI, Query, HTTPException
import re
import logging
from infrastructure import create_infrastructure
from destroy_infrastructure import delete_infrastructure

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

CLIENT_STORE_PATTERN = re.compile(r"^[a-z][a-z0-9]+$")

def validate_client_store(client_store: str):
    if not CLIENT_STORE_PATTERN.match(client_store):
        raise HTTPException(
            status_code=400,
            detail="Invalid client_store. Must be lowercase alphanumeric, no special characters, and start with a letter."
        )

@app.get("/create-client-infrastructure", status_code=201)
def create_client_infrastructure(client_store: str = Query(..., description="Client store identifier")):
    try:
        validate_client_store(client_store)
        logger.info(f"Creating infrastructure for client_store: {client_store}")
        create_infrastructure(client_store)
        return {"message": f"Infrastructure created for {client_store}"}
    except HTTPException as e:
        logger.error(f"Validation error: {e.detail}")
        raise
    except Exception as e:
        logger.exception("Unexpected error while creating infrastructure")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/delete-infrastructure", status_code=200)
def delete_client_infrastructure(client_store: str = Query(..., description="Client store identifier")):
    try:
        validate_client_store(client_store)
        logger.info(f"Deleting infrastructure for client_store: {client_store}")
        delete_infrastructure(client_store)
        return {"message": f"Infrastructure deleted for {client_store}"}
    except HTTPException as e:
        logger.error(f"Validation error: {e.detail}")
        raise
    except Exception as e:
        logger.exception("Unexpected error while deleting infrastructure")
        raise HTTPException(status_code=500, detail="Internal Server Error")



#to run  fastapi uvicorn infrastructure_wrapper_api:app --reload