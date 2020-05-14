import time

from django.db import models
import numpy as np
from PIL import Image
from rawkit.raw import Raw


#auth_user.id

class ImageUpload(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField()


class ImageConverter():

    def convert_file(self, path, destination):
        '''Converts path.cr2 File and returns JPEG'''
        raw_image = Raw(path)
        buffered_image = np.array(raw_image.to_buffer())
        if raw_image.metadata.orientation == 0:
            converted_image = Image.frombytes('RGB', (raw_image.metadata.width, raw_image.metadata.height), buffered_image)
        else:
            converted_image = Image.frombytes('RGB', (raw_image.metadata.height, raw_image.metadata.width), buffered_image)

        converted_image.save(destination, format='jpeg')
        converted_image.thumbnail((250,250),Image.ANTIALIAS)
        converted_image.save(destination[:-4]+'-thumb.jpg',format='JPEG',quality=80)




    def thumbnail(self,source,destination):
        SIZE = (315, 320)
        im = Image.open(source)
        im.convert('RGB')
        im.thumbnail(SIZE, Image.ANTIALIAS)
        im.save(destination, 'JPEG', quality=80)




