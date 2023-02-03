FROM iqtlabs/edgetech-core:latest
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY ./s3_uploader_pub_sub.py .
ENTRYPOINT [ "python3", "-u", "s3_uploader_pub_sub.py" ]
