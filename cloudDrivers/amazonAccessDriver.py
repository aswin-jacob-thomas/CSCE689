import json
import logging
import uuid

import boto3
from botocore.exceptions import ClientError
logger = logging.getLogger(__name__)

class AmazonS3Driver(cloudDriver):
    def __init__(self, cloudId, accessKey, secretKey):
    	self.default_bucket_name = 'csce689cpc'
        self.cloudId = cloudId
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.s3_resource = ''
        self.bucket_name = ''

        if cloudId == 'cloud1':
        	self.bucket_name = default_bucket_name + "-coc1"
        elif cloudId == 'cloud2':
        	self.bucket_name = default_bucket_name + "-coc2"
        elif cloudId == 'cloud3':
        	self.bucket_name = default_bucket_name + "-coc3"
        elif cloudId == 'cloud4':
        	self.bucket_name = default_bucket_name + "-coc4"

    def initialize(self):
    	self.s3_resource = boto3.resource('s3', aws_access_key_id=ACCESS_KEY,
        	aws_secret_access_key=SECRET_KEY)
    	s3 = self.s3_resource
    	try:
    		bucket = s3.create_bucket(Bucket=self.bucket_name)
    		bucket.wait_until_exists()

    	except ClientError as error:
        	logger.exception("Couldn't create bucket named '%s' in region=%s.",
        		name, region)
        	if error.response['Error']['Code'] == 'IllegalLocationConstraintException':
       			logger.error("When the session Region is anything other than us-east-1, "
                         "you must specify a LocationConstraint that matches the "
                         "session Region. The current session Region is %s and the "
                         "LocationConstraint Region is %s.",
                         s3.meta.client.meta.region_name, region)
        	raise error
    	else:
        	return bucket



    def read(self, bucketName, fileName):
    	try:
	        obj = self.s3_resource.Object(bucketName.name, fileName)
			body = obj.get()['Body'].read()
		except clientError:
        	logger.exception(("Couldn't get object '%s' from bucket '%s'.",
                          fileName, bucketName))
        	raise
    	else:
        	return body


    def write(self, bucketName, data, fileName):
    	try:
	        obj = self.s3_resource.Object(bucketName.name, fileName)
			obj.put(Body=data)
			obj.wait_until_exists()
		except ClientError:
        	logger.exception("Couldn't put object '%s' to bucket '%s'.",
                         fileName, bucketName)
        	raise
        else:
        	return
