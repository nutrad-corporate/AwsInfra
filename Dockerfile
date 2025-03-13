# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY .env /app/
COPY requirements.txt /app/
COPY main.py /app/
COPY AWS_API_GATEWAY.py /app/
COPY AWS_Batch.py /app/
COPY AWS_Lambda.py /app/
COPY delete_client.py /app/
COPY infrastructure.py /app/
COPY s3_bucket.py /app/
COPY destroy_infrastructure.py /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 80
EXPOSE 8080

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
