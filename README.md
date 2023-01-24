# Edgetech S3 Uploader
A module to upload object to S3 storage.

## Enviroment Variables
SEND_DATA_TOPIC Topic to send events to
C2_TOPIC        Topic to issue sync command with message "S3 SYNC FILES" payload
DATA_DIR        Data Directory to sync
INCLUDE_FILES   Only sync files of this filetype
MQTT_IP         MQTT Broker IP

## TODO
- Docker Secrets for AWS Credentials
- Upload a single file
- Check for errors and upload status -> output to MQTT