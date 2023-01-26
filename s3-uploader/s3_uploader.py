import time
import json
import os
#import boto3
from time import sleep
from datetime import datetime
from typing import Any, Dict
import subprocess
import schedule

import paho.mqtt.client as mqtt

from base_mqtt_pub_sub import BaseMQTTPubSub


class S3Uploader(BaseMQTTPubSub):
    """This class starts a AWS S3 sync when triggered by C2 and publishes status to MQTT.
    Args:
        BaseMQTTPubSub (BaseMQTTPubSub): parent class written in the EdgeTech Core module
    """
    def __init__(
        self,
        send_data_topic: str,
        c2c_topic: str,
        include_files: str,
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
            include_files (str): REGEX match for files to include (Ex: *.wav)
            target_dir (str): Internal container directory path to sync (Es: /sensor-data/).
            s3_bucket (str): name of AWS S3 bucket
            debug (bool, optional): If the debug mode is turned on, log statements print to stdout.
        """

        super().__init__(**kwargs)

        self.send_data_topic = send_data_topic
        self.c2c_topic = c2c_topic

        self.target_dir = target_dir
        self.s3_bucket = s3_bucket
        self.include_files = include_files

        self.debug = debug

        self.sync_process = None

        #self.s3_client=boto3.client('s3_client')

        self.connect_client()
        sleep(1)
        self.publish_registration("S3 Uploader Registration")

    def _send_data(self, data) -> None:
        self.publish_to_topic(self.send_data_topic, json.dumps(data))

    def _c2c_callback(
        self: Any, _client: mqtt.Client, _userdata: Dict[Any, Any], msg: Any
    ) -> None:
        '''Upon message from C2, this callback uses the AWS cli to sync a directory
        with a specified S3 Bucket
        '''
        c2c_payload = json.loads(str(msg.payload.decode("utf-8")))
        if c2c_payload["msg"] == "S3 SYNC FILES":
            self._send_data(f"syncing dir: {self.target_dir}")
            print("Callback recieved...")

            try:
                #Use AWS CLI to sync to S3 Bucket
                cmd_flags=""
                if self.include_files != "":
                    cmd_flags=cmd_flags + f'--exclude "*" --include {self.include_files}'
                sync_cmd = f'aws s3 sync {self.target_dir} s3://{self.s3_bucket} ' + cmd_flags
                print(sync_cmd)
                self._send_data(sync_cmd)#+ cmd_flags)
                self.sync_process = subprocess.Popen(
                    sync_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                #Wait for process to complete
                while self.sync_process.poll() is None:
                    time.sleep(0.1)
                stdout,stderr=self.sync_process.communicate()
                
                # Print Sucess or failure message
                if self.sync_process.returncode == 0:
                    self._send_data(stdout.decode())
                    print(stdout)
                else:
                    self._send_data(stderr.decode())
                    print(stderr)
                    
            except Exception as e:
                if self.debug:
                    print(e)


    def main(self: Any) -> None:
        """Main loop and function that setup the heartbeat to keep the TCP/IP
        connection alive and publishes the data to the MQTT broker and keeps the
        main thread alive."""

        #Schedule heartbeat
        schedule.every(10).seconds.do(
            self.publish_heartbeat, payload="S3 Uploader Heartbeat"
        )

        #Register Callback from C2
        self.add_subscribe_topic(self.c2c_topic, self._c2c_callback)

        while True:
            try:
                schedule.run_pending()
                time.sleep(0.001)
            except KeyboardInterrupt:
                if self.debug:
                    print("s3-uploader application stopped!")

            except Exception as e:
                if self.debug:
                    print(e)


if __name__ == "__main__":
    s3_uploader = S3Uploader(
        send_data_topic=os.environ.get("SEND_DATA_TOPIC"),
        c2c_topic=os.environ.get("C2_TOPIC"),
        include_files=os.environ.get("INCLUDE_FILES"),
        target_dir=os.environ.get("TARGET_DIR"),
        s3_bucket=os.environ.get("S3_BUCKET"),
        mqtt_ip=os.environ.get("MQTT_IP"),
    )
    s3_uploader.main()