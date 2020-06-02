import time

from django.db import models
import numpy as np
from PIL import Image
from rawkit.raw import Raw
from DjangoProject.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_MEDIA_BUCKET_NAME, MEDIA_FILES_ON_S3
import boto3
from io import BytesIO
from OnlineImageConverter.storage_backends import CustomMediaStorage

class Album(models.Model):
    album_id = models.IntegerField()
    album_name = models.TextField()
    album_user_id = models.IntegerField()


#auth_user.id

class ImageUpload(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField()


class ImageConverter():

    def convert_image(self, cr2_file):
        """Takes a CR2 file and returns a JPG file"""

        pass


    def convert_file(self, path, destination):
        '''Converts path.cr2 File and returns JPEG'''
        raw_image = Raw(path)
        buffered_image = np.array(raw_image.to_buffer())
        print('reading raw image')
        if raw_image.metadata.orientation == 0:
            converted_image = Image.frombytes('RGB', (raw_image.metadata.width, raw_image.metadata.height), buffered_image)
        else:
            converted_image = Image.frombytes('RGB', (raw_image.metadata.height, raw_image.metadata.width), buffered_image)

        if MEDIA_FILES_ON_S3:
            s3 = boto3.resource('s3',
                                region_name="us-west-2",
                                aws_access_key_id=AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                                )

            user_id, album, file = path.split('/')[-3:]
            new_file_name = file[:-4]+'_converted.jpg'
            new_key = '/user_uploads/{}/{}/{}'.format(user_id,album,new_file_name)

            # 'image' is a PIL image object.
            print('creating buffer')
            imageBuffer = BytesIO() #create Buffer Object
            converted_image.save(imageBuffer, format='JPEG')     #save image into Buffer

            print('saving to S3')
            custom_media_storage = CustomMediaStorage()
            custom_media_storage.save(new_key, imageBuffer)     #save Buffer to S3
            file_url = custom_media_storage.url(new_key)
            print(file_url)

            # imageFile = custom_media_storage.open(imageFileName, 'wb')
            # imageFile.write(imageBuffer.getvalue())
            # imageFile.flush()
            # imageFile.close()

            return file_url

        else:
            converted_image.save(destination, format='jpeg')
            converted_image.thumbnail((250,250),Image.ANTIALIAS)
            converted_image.save(destination[:-4]+'-thumb.jpg',format='JPEG',quality=80)




    def thumbnail(self,source,destination):
        SIZE = (315, 320)
        im = Image.open(source)
        im.convert('RGB')
        im.thumbnail(SIZE, Image.ANTIALIAS)
        im.save(destination, 'JPEG', quality=80)




