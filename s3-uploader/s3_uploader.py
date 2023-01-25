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
    def __init__(
        self,
        send_data_topic: str,
        c2c_topic: str,
        data_dir: str,
        include_files: str,
        target_dir: str,
        s3_bucket: str,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.send_data_topic = send_data_topic
        self.debug = debug
        self.c2c_topic = c2c_topic

        self.target_dir = target_dir
        self.s3_bucket = s3_bucket
        self.include_files = include_files

        self.sync_process = None

        self.s3_client=boto3.client('s3_client')

        self.connect_client()
        sleep(1)
        self.publish_registration("S3 Uploader Registration")

    def _send_data(self, data) -> None:
        self.publish_to_topic(self.send_data_topic, json.dumps(data))

    def _c2c_callback(
        self: Any, _client: mqtt.Client, _userdata: Dict[Any, Any], msg: Any
    ) -> None:
        c2c_payload = json.loads(str(msg.payload.decode("utf-8")))
        if c2c_payload["msg"] == "S3 SYNC FILES":
            self._send_data(f"syncing dir: {self.target_dir}")
            self._s3_sync_dir()

    def _s3_sync_dir(self: Any) -> None:
        try:
            cmd_flags=""
            if self.include_files != "":
                cmd_flags=cmd_flags + f"--include {self.include_files}"

            sync_cmd = (
                f"aws s3 sync {self.target_dir} s3://{self.s3_bucket} " + cmd_flags
            )
            self.sync_process = subprocess.Popen(
                sync_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        except Exception as e:
            if self.debug:
                    print(e)


    #TODO: function to upload a single file 
    #def _s3_upload_file(self: Any) -> None:
    #    self.upload_object_name=os.path.basename(filename)
    #    try:
    #        res = self.s3_client.upload_file(filename,'bucket_name',self.upload_object_name)
    #    except Exception as e:
    #        if self.debug:
    #                print(e)

    def main(self: Any) -> None:

        schedule.every(10).seconds.do(
            self.publish_heartbeat, payload="S3 Uploader Heartbeat"
        )

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