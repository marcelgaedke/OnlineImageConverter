from storages.backends.s3boto3 import S3Boto3Storage
from DjangoProject.settings import AWS_MEDIA_BUCKET_NAME
class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False

class AWS_S3_MediaStorage(S3Boto3Storage):
    bucket_name = AWS_MEDIA_BUCKET_NAME
    custom_domain = '{}.s3.amazonaws.com'.format(bucket_name)
    location = ''
    file_overwrite = False
