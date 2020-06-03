import boto3
import os
from storages.backends.s3boto3 import S3Boto3Storage
from DjangoProject.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_MEDIA_BUCKET_NAME


class FileUpload():
    file_list=[]
    num_files=0
    album = None
    error=False


class AWS_S3_MediaStorage(S3Boto3Storage):
    bucket_name = AWS_MEDIA_BUCKET_NAME
    custom_domain = '{}.s3.amazonaws.com'.format(bucket_name)
    location = ''
    file_overwrite = False


def save_file_on_s3(file, album):
    file_directory_within_bucket = '/user_uploads/{}/{}'.format(album.album_user_id, album.album_id)

    file_path_within_bucket = os.path.join(
        file_directory_within_bucket,
        file.name
    )
    aws_s3_media_storage = AWS_S3_MediaStorage()
    aws_s3_media_storage.save(file_path_within_bucket, file)
    file_url = aws_s3_media_storage.url(file_path_within_bucket)
    file_name = file_url.split('/')[-1]
    return (file_name, file_url)


def get_album_content(album):
    s3 = boto3.resource('s3',
                        region_name="us-west-2",
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                        )

    bucket = s3.Bucket(AWS_MEDIA_BUCKET_NAME)
    content = []
    for obj in bucket.objects.filter(Prefix=album.album_s3_bucket_prefix):     #Get all keys for album
        file_name = obj.key.split('/')[-1]
        file_url = album.album_url + file_name
        content.append({'file_url':file_url, 'file_name':file_name})
    return content