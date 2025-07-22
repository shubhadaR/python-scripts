# Bridge Service

This is a Flask-based alert processing service that integrates with GLPI, a ticketing system, to create and manage tickets for incoming alerts. The service is designed to process incoming JSON payloads containing alerts, extract relevant information, and perform actions based on the alerts.

---

First clone the repo

```
git clone http://git.monitoring.bfsgodirect.com/managed-cloud/central-observability-platform/helm-manifests.git
```

Now go inside dashboard folder

```
cd /helm-manifests/python_glpi_webhook
```

Here you will see following files

```

├── Chart.yaml
├── Dockerfile
├── app
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   └── requirements.txt
├── README.md
├── templates
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── hpa.yamltemplates
│   └── service.yaml
├── values.yaml
```

# Dockerized Python Application

This Dockerfile sets up a Python environment based on Alpine Linux (version 3.18) for running a Python application.

1.  Dockerfile for python application.
2.  Build a Docker image for the ARM64 architecture and push it to an Amazon Elastic Container Registry (ECR) repository. The provided command uses Docker BuildKit to build the image and tags it with a specific name for later use.
3.  Configuration for bridge_service.

## **Step 1:  Dockerfile for python application.**

---

Dockerfile used to build a container image for a Python application. The Dockerfile contains instructions on how to create an environment, install dependencies, and run the Python application.

## **Dockerfile Overview**

The provided Dockerfile starts with a base image (**python:alpine3.18**), sets up a working directory, copies application files, installs dependencies, and specifies the command to run when the container is started.

### **Base Image**

> FROM python:alpine3.18

This line specifies the base image to use for building the container. In this case, it's based on Alpine Linux with Python 3.18 installed.

### **Working Directory**

> WORKDIR /app

The **WORKDIR** instruction sets the working directory within the container to **/app**. This is where the application files will be placed and where the application will run.

### **Copy Application Files**

> COPY app/\* /app

These lines use the **COPY** instruction to copy the application files (**app.py**, **config.py**, **models.py**, and **requirements.txt**) from the local directory into the **/app** directory within the container.

### **Package and Dependency Installation**

> RUN apk upgrade  
> RUN apk update  
> RUN apk add musl-dev mariadb-dev gcc  
> RUN pip install -r requirements.txt

These lines are responsible for updating the Alpine Linux package index, upgrading packages, and installing system dependencies (**musl-dev**, **mariadb-dev**, and **gcc**) required for some Python packages. It then installs the Python dependencies listed in **requirements.txt** using **pip**.

#### **Python Application Dependencies**

This **requirements.txt** file specifies the Python packages and their versions required to run your Python application. These packages will be installed using **pip** to ensure that your application has all the necessary dependencies. Please review this file to ensure compatibility with your application.

### **Package List**

**mysqlclient**

- Description: A MySQL database connector for Python.
- Usage: Allows your application to interact with a MySQL database.

**flask>=2.0.1**

- Description: The Flask web framework for Python.
- Version Specification: Greater than or equal to 2.0.1.
- Usage: Flask is a lightweight web framework used to build web applications and APIs.

**requests>=2.26**

- Description: The Requests library for making HTTP requests in Python.
- Version Specification: Greater than or equal to 2.26.
- Usage: Allows your application to send HTTP requests and interact with web services.

**flask-cors>=4.0.0**

- Description: Flask-CORS is an extension for Flask that handles Cross-Origin Resource Sharing (CORS) for your API.
- Version Specification: Greater than or equal to 4.0.0.
- Usage: Useful for handling cross-origin requests when building web applications with Flask.

**retrying>=1.3.4**

- Description: A library for retrying operations with exponential backoff.
- Version Specification: Greater than or equal to 1.3.4.
- Usage: Helpful for gracefully handling transient failures in your application.

**python-decouple**

- Description: A library for handling application settings in a clean and practical way, typically using configuration files.
- Usage: Simplifies the management of configuration settings in your application.

**flask_sqlalchemy**

- Description: An extension for Flask that simplifies database integration, allowing you to use SQLAlchemy with your Flask application.
- Usage: Enables your Flask application to interact with relational databases using SQLAlchemy.

### **Command to Run the Application**

> CMD \[ "python3", "app.py" \]

The **CMD** instruction specifies the command that will be executed when the container is started. In this case, it runs the Python script **app.py** using **python3**.

## **Step 2:   Build a Docker image for the ARM64 architecture and push it to an Amazon Elastic Container Registry (ECR) repository. The provided command uses Docker BuildKit to build the image and tags it with a specific name for later use.**

---

### **Prerequisites**

1.  Make sure you have Docker installed on your system before building and running this Docker image.
2.  An AWS account with necessary permissions to access the ECR service.
3.  AWS Command Line Interface (CLI) installed and configured with appropriate AWS credentials.
4.  An existing ECR repository (**266189958330.dkr.ecr.ap-southeast-1.amazonaws.com/glpi-python-webhook** in this example) where you want to push the image.

### **Command Overview**

The command you provided performs the following tasks:

1.  It sets the **DOCKER_BUILDKIT** environment variable to enable Docker BuildKit, which is a modern build subsystem for Dockerthat provides enhanced functionality for building Docker images.
2.  It specifies the target platform as **linux/arm64** to build an image for ARM64 architecture.
3.  It tags the resulting Docker image with the name **266189958330.dkr.ecr.ap-southeast-1.amazonaws.com/glpi-python-webhook:test-v1**.
4.  It uses the current directory (**.**) as the build context, which typically contains a Dockerfile and any required application files.

### **Building the Docker Image**

To build the Docker image, navigate to the directory containing your **Dockerfile** and run the following command:

> ```
> $ sudo DOCKER_BUILDKIT=1 docker build --platform=linux/arm64 -t <ecr_repo_url>:<tag> .
>
> Example :- sudo DOCKER_BUILDKIT=1 docker build --platform=linux/arm64 -t 266189958330.dkr.ecr.ap-southeast-1.amazonaws.com/glpi-python-webhook:test-v1 .
> ```

### **LOGIN TO ECR**

#### **Command Overview**

The command you provided performs the following tasks:

1.  It retrieves an authentication token (password) from AWS ECR for the specified AWS region (**ap-southeast-1** in this example).
2.  It passes this token securely to the Docker **login** command, along with the ECR registry URL and your AWS username to authenticate Docker with the ECR service.

> ```
> $ aws ecr get-login-password --region <region> | sudo docker login --username AWS --password-stdin <ecr_repo>
>
> Example :- aws ecr get-login-password --region ap-southeast-1 | sudo docker login --username AWS --password-stdin 266189958330.dkr.ecr.ap-southeast-1.amazonaws.com
> ```

### **PUSH IMAGE TO ECR**

#### **Command Overview**

The command you provided performs the following tasks:

1.  **docker push**: The core command used to push Docker images.
2.  **NAME\[:TAG\]**: Specifies the name of the image to push along with an optional tag. The name typically includes the container registry URL (e.g., `266189958330.dkr.ecr.ap-southeast-1.amazonaws.com/glpi-python-webhook`) and, optionally, a specific image tag(`test-v1`).

> ```
> $ sudo docker push 266189958330.dkr.ecr.ap-southeast-1.amazonaws.com/glpi-python-webhook:test-v1
> ```

### **Step 3 : Configuration for bridge_service.**

---

configuration file used for the GLPI Python Webhook application. The configuration file allows you to define various parameters and settings required for the operation of the application.

### **Configuration Overview**

The configuration file is structured in YAML format and consists of different sections, each containing specific settings related to the application, GLPI integration, and database connection.

### **Region**

> region :  \<region>

- Specifies the AWS region where the application is deployed. In this example, it's set to **ap-south-1**.

### **Image**

> image:  
>  ecrRepo: 266189958330.dkr.ecr.ap-southeast-1.amazonaws.com/glpi-python-webhook  
>  pullPolicy: IfNotPresent  
>  tag: test-v1

- **ecrRepo**: Defines the Amazon Elastic Container Registry (ECR) repository URL where the Docker image for the application is hosted.
- **pullPolicy**: Specifies the image pull policy, which is set to **IfNotPresent**, meaning the image is only pulled if it's not already present locally.
- **tag**: Sets the Docker image tag. In this example, it's tagged as `**test-v1**`.

### **GLPI Configuration**

> glpi:  
> glpiUrl: ""  
> glpiUser: ""  
> glpiAppToken: ""  
> glpiUserToken: ""  
> ivrEndpointUrl: ""  
> ticket_threshold_duration: ""  
> ticket_threshold_count: ""  
> close_ticket_threshold_duration: ""

- **glpiUrl**: Specifies the URL of the GLPI server's API endpoint.
- **glpiUser**: Provides the username for authentication with GLPI.
- **glpiAppToken**: Defines the GLPI application token for authentication.
- **glpiUserToken**: Sets the GLPI user token for authentication.
- **ivrEndpointUrl**: Specifies the URL for the IVR (Interactive Voice Response) endpoint.
- **ticket_threshold_duration**: Defines the threshold duration (in seconds) for ticket processing.
- **ticket_threshold_count**: Sets the threshold count for ticket processing.
- **close_ticket_threshold_duration**:  Defines the treshhold duration to check alert with resolved state  to close ticket

### **Database Configuration**

> database:  
> db_username: ""  
> db_password: ""  
> db_host: ""  
> db_name: ""  
> tickets_table_name: ""  
> alert_history_table_name: ""

- **db_username**: Specifies the username for the database connection.
- **db_password**: Sets the password for the database connection.
- **db_host**: Defines the hostname or endpoint of the database server.
- **db_name**: Specifies the name of the database to be accessed.
- **tickets_table_name**: Sets the name of the  tickets table within the database where all  created tickets will be stored and removed once ticket is closed.
- **alert_history_table_name**:  Sets the name of the  alert_history table within the database where data for specific time is stored to check occuarance of alerts.

### **Port Expose**

> port_expose: 8080

- Specifies the port on which the application will expose its services. In this example, it's set to **8080**.

### **Bridge service Configmap**

This ConfigMap, named \`bridge-service-configmap\`, is designed to serve as a configuration resource for the Bridge service. It contains mappings of resource names and their corresponding identifier keys, which are essential for resource identification within the Bridge service. These mappings are essential for integrating and monitoring different AWS resources.

#### Configuration Details

The \`resource_mapping.json\` file within this ConfigMap contains an array of resource mappings, each having the following structure:

> {  
>  "resource_name": "Resource Name",  
>  "identifierkey": "Identifier Key"  
> }

Here's an explanation of the key elements:

- **resource_name**: This field specifies the name of the AWS resource. Examples include "EC2," "RDS," "Lambda," and more.
- **identifierkey**: This field specifies the key or attribute used to uniquely identify instances of the resource. For instance, for an EC2 instance, it could be "instance," while for an RDS instance, it could be "dimension_DBInstanceIdentifier."

**Below is an example of a resource mapping for an EC2 instance:**

> {  
>  "resource_name": "EC2",  
>  "identifierkey": "instance"  
> }

As resources will increase we will need to add a new entry to the **resource_mapping** array with the **resource_name** and **identifierkey** for the new resource.   
For example:

> {  
>  "resource_name": "NewResource",  
>  "identifierkey": "newIdentifier"  
> }

Save the changes to the ConfigMap.

## **Installation Steps**

Follow these steps to install the GLPI Python Webhook application using Helm:

1\. Open a terminal window.

2\. Navigate to the directory containing the Helm chart (e.g., **python_glpi_webhook**).

3\. Run the Helm installation command:

> $ helm install bridge_service ./python_glpi_webhook -n observability

- Replace **bridge_service** with your preferred release name if desired.

4\. Wait for Helm to complete the installation. You will see output indicating the installation progress.

5\. Once the installation is successful, you can verify the deployment by running:

> $ kubectl get pods -n observability

This will show you the pods running in the **observability** namespace, including those associated with the GLPI Python Webhook application.

## **Cleanup**

To uninstall the GLPI Python Webhook application and delete the release, you can use the following Helm command:

> helm uninstall bridge_service -n observability

Replace **glpi** with your release name if you used a different name during installation.
