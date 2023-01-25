# Edgetech S3 Uploader
A module to upload object to S3 storage.

## Enviroment Variables
SEND_DATA_TOPIC Topic to send events to
C2_TOPIC        Topic to issue sync command with message "S3 SYNC FILES" payload
DATA_DIR        Data Directory to sync
INCLUDE_FILES   Only sync files of this filetype
MQTT_IP         MQTT Broker IP

Add the following to `.profile` to pass your specific AWS credentials.
```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-east-2
``` 

## TODO
- Docker Secrets for AWS Credentials
- Upload a single file
- Check for errors and upload status -> output to MQTT
- Move env variables to env file