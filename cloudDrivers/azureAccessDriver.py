from google.cloud import storage

# Set gloud credentials.
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/file/path/to/gcloud.json" 

class AzureStorageDriver(cloudDriver):
    def __init__(self, cloudId, serviceAccountFileName):
    	self.default_bucket_name = 'csce689cpc'
        self.cloudId = cloudId
        self.storage_client = ''

        self.service_account_file = serviceAccountFileName

        if cloudId == 'cloud1':
        	self.bucket_name = self.default_bucket_name + "-coc1"
        elif cloudId == 'cloud2':
        	self.bucket_name = self.default_bucket_name + "-coc2"
        elif cloudId == 'cloud3':
        	self.bucket_name = self.default_bucket_name + "-coc3"
        elif cloudId == 'cloud4':
        	self.bucket_name = self.default_bucket_name + "-coc4"


    def initialize(self):
        self.storage_client = storage.Client.from_service_account_json(
            self.service_account_file)
        # buckets = list(self.storage_client.list_buckets())
        # print(buckets)	
        bucket = storage_client.create_bucket(bucket_or_name=self.bucket_name)
        return bucket.name

    def read(self, bucketName, fileName):
    	bucket = self.storage_client.bucket(bucketName)
        blob = bucket.blob(fileName)
        return blob.download_as_string()

    def write(self, bucketName, data, fileName):
        bucket = self.storage_client.get_bucket(bucketName)
        blob = bucket.blob(fileName)
        # ref: https://googleapis.dev/python/storage/latest/blobs.html
        blob.upload_from_string(data)
        return
