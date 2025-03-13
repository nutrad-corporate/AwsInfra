**Steps to run the Infrastructure API using AWS EC2**
Step 1: Create an EC2 instance, by selecting OS as “Ubuntu” and using key-pair as “awsInfra” and then save the awsInfra.pem into “C:\Users\<user-name>\.ssh\<....pem>”

**Step 2: Open the terminal and connect to EC2 using the SSH:**
ssh –i “C:\Users\<user-name>\.ssh\awsInfra.pem” ubuntu@<public_ip>

e.g., ssh –i “C:\Users\Anuj Bisht\.ssh\awsInfra.pem” ubuntu@13.233.174.51

**Step 3: clone the git repository**
e.g., git clone <git-repo-url>

**Step 4: Download the Docker*
sudo snap install docker

**Step 5: Create the docker image**
sudo docker build –t <image-name> .

**Step 6: Run the Docker Image**
<!-- sudo docker run -e MONGODB_URI="mongodb://nuadmin:H9ck668ixt3\!@44.211.106.255:19041/"
-e AWS_ACCESS_KEY_ID=""
-e AWS_SECRET_ACCESS_KEY=""
-e AWS_DEFAULT_REGION="" -p 80:80 
-->
awsinfra  
