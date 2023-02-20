"""This file contains the S3UploaderPubSub which class which is a child class of BaseMQTTPubSub.
It uses the AWS CLI to push data up to S3 based on a trigger from the C2 command.
"""
import json
import os

from time import sleep
from typing import Any, Dict
import subprocess
import schedule

import paho.mqtt.client as mqtt

from base_mqtt_pub_sub import BaseMQTTPubSub


class S3UploaderPubSub(BaseMQTTPubSub):
    """The S3UploaderPubSub starts a AWS S3 sync when triggered by C2 and publishes status to MQTT.
    Args:
        BaseMQTTPubSub (BaseMQTTPubSub): parent class written in the EdgeTech Core module
    """

    def __init__(
        self,
        send_data_topic: str,
        c2c_topic: str,
        target_dir: str,
        s3_bucket: str,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        """The S3Uploader constructor takes topic, callback topic, and information about the
        sync directory and S3 bucket.
        Args:
            send_data_topic (str): MQTT topic to publish the status to.
            c2c_topic (str): C2 topic to initiate sync
            target_dir (str): Internal container directory path to sync (Es: /sensor-data/).
            s3_bucket (str): name of AWS S3 bucket
            debug (bool, optional): If the debug mode is turned on, log statements print to stdout.
        """
        # override BaseMQTTPubSub keyword arguments
        super().__init__(**kwargs)

        # assigning class attributes
        self.send_data_topic = send_data_topic
        self.c2c_topic = c2c_topic

        self.target_dir = target_dir
        self.s3_bucket = s3_bucket

        self.debug = debug

        self.sync_process = None

        # setting up MQTT client
        self.connect_client()
        sleep(1)
        self.publish_registration("S3 Uploader Registration")

    def _send_data(self: Any, data: Dict[str, str]) -> None:
        self.publish_to_topic(self.send_data_topic, json.dumps(data))

    def _c2c_callback(
        self: Any, _client: mqtt.Client, _userdata: Dict[Any, Any], msg: Any
    ) -> None:
        """Upon message from C2, this callback uses the AWS CLI to sync a directory
        with a specified S3 Bucket
        """
        # decode C2 payload
        c2c_payload = json.loads(str(msg.payload.decode("utf-8")))

        # if C2 message payload is S3 SYNC, trigger the sync process
        if c2c_payload["msg"] == "S3 SYNC":
            # Essentially logging using MQTT
            self._send_data(f"syncing dir: {self.target_dir}")
            try:
                # Use AWS CLI to sync to S3 Bucket
                # cmd_flags = ""
                cmd_flags = '--exclude "*" --include "*.json" --include "*.flac"'
                sync_cmd = (
                    f"aws s3 sync {cmd_flags} {self.target_dir} s3://{self.s3_bucket}"
                )

                # using subprocess to call the command
                self.sync_process = subprocess.Popen(sync_cmd, shell=True)
                stdout, stderr = self.sync_process.communicate()

                # Print Success or failure message
                if self.sync_process.returncode == 0:
                    self._send_data(stdout)
                    if self.debug:
                        print(stdout)
                else:
                    self._send_data(stderr)
                    if self.debug:
                        print(stderr)

            except KeyboardInterrupt as exception:
                if self.debug:
                    print(exception)

    def main(self: Any) -> None:
        """Main loop and function that setup the heartbeat to keep the TCP/IP
        connection alive and publishes the data to the MQTT broker and keeps the
        main thread alive."""

        # Schedule heartbeat
        schedule.every(10).seconds.do(
            self.publish_heartbeat, payload="S3 Uploader Heartbeat"
        )

        # Register Callback from C2
        self.add_subscribe_topic(self.c2c_topic, self._c2c_callback)

        while True:
            try:
                # flush pending scheduled tasks
                schedule.run_pending()
                sleep(0.001)
            except KeyboardInterrupt as exception:
                if self.debug:
                    print(exception)


if __name__ == "__main__":
    s3_uploader = S3UploaderPubSub(
        send_data_topic=str(os.environ.get("SEND_DATA_TOPIC")),
        c2c_topic=str(os.environ.get("C2_TOPIC")),
        target_dir=str(os.environ.get("TARGET_DIR")),
        s3_bucket=str(os.environ.get("S3_BUCKET")),
        mqtt_ip=str(os.environ.get("MQTT_IP")),
    )
    s3_uploader.main()
