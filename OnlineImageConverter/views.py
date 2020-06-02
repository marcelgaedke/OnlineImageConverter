import os
import boto3

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from OnlineImageConverter.storage_backends import CustomMediaStorage
from OnlineImageConverter.models import ImageConverter, ImageUpload
from DjangoProject.settings import BASE_DIR, MEDIA_FILES_ON_S3, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_MEDIA_BUCKET_NAME
import multiprocessing
import time

from PIL import Image

temp_path = BASE_DIR + '/OnlineImageConverter/static/OnlineImageConverter/temp/'

def index(request):
    return HttpResponse("Index")


def welcome(request):

    return render(request, 'OnlineImageConverter/welcome.html')

def start(request):
    keys = set()
    if request.user.is_authenticated:
        user_id=request.user.id
        # Get list of Albumsfor this user
        s3 = boto3.resource('s3',
                            region_name="us-west-2",
                            aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                            )
        # S3 list all keys with the prefix 'photos/'
        # bucket = s3.Bucket('django-media-public-1337')
        bucket = s3.Bucket(AWS_MEDIA_BUCKET_NAME)
        bucket_prefix = 'user_uploads/{}/'.format(user_id)
        for obj in bucket.objects.filter(Prefix=bucket_prefix):
            album_name = obj.key.split('/')[2]
            if album_name != 'Uploads':
                keys.add(obj.key.split('/')[2])

    else:
        user_id="none"

    context = {
        'user_id': user_id,
        'keys': keys
    }
    return render(request, 'OnlineImageConverter/start.html', context)


def album(request):
    album_name = request.GET['album_name']
    user_id = request.user.id

    s3 = boto3.resource('s3',
                        region_name="us-west-2",
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                        )
    bucket = s3.Bucket(AWS_MEDIA_BUCKET_NAME)
    bucket_prefix = 'user_uploads/{}/{}/'.format(user_id,album_name)
    url_prefix = 'https://django-media-public-1337.s3.amazonaws.com/'   #/user_uploads/1/Birthday2019/sky.jpg'
    image_list = []
    for obj in bucket.objects.filter(Prefix=bucket_prefix):
        image_list.append(url_prefix+obj.key)

    context = {
        'album_name':album_name,
        'image_list':image_list,
    }
    return render(request, "OnlineImageConverter/album.html", context)

def upload(request):
    user_id = request.user.id
    return render(request, 'OnlineImageConverter/upload.html', {'user_id': user_id,
                                                                    'env': os.getenv('AWS_STORAGE_BUCKET_NAME')})

# Object Types:
# with open(...,'rb'):      io.BufferedReader
# uploaded_file.file        <class 'io.BytesIO'>
# Raw(path)                 <class 'rawkit.raw.Raw'>
# rawimg.to_buffer()        <class 'bytearray'>

def upload_result_test(request):
    file = request.FILES['file_uploads']
    #img = Image.open(uploaded_file.file,'r')

    fs = FileSystemStorage()
    fs.location = os.path.join(settings.BASE_DIR, '/UploadedImages/')
    fs.save(file.name, file)

    # if raw_image.metadata.orientation == 0:
    #     converted_image = Image.frombytes('RGB', (raw_image.metadata.width, raw_image.metadata.height), buffered_image)
    # else:
    #     converted_image = Image.frombytes('RGB', (raw_image.metadata.height, raw_image.metadata.width), buffered_image)

    #img.save('/home/kidneybean/Pictures/conv/conv2.jpg', format='JPEG')
    #img.close()

    return HttpResponse('Type:')
    # response = requests.get(url)
    # img = Image.open(BytesIO(response.content))

def upload_result(request):
    if request.method == 'POST' and len(request.FILES.getlist('file_uploads'))>0:
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = "none"

        file_urls = []
        for file in request.FILES.getlist('file_uploads'):
            if request.user.is_authenticated:
                if MEDIA_FILES_ON_S3:
                    s3 = boto3.resource('s3',
                                        region_name="us-west-2",
                                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                                        )
                    #organize a path for the file in bucket
                    #file_directory_within_bucket = 'user_upload_files/{username}'.format(username=requests.user)
                    album_name = 'Uploads'
                    file_directory_within_bucket = '/user_uploads/{}/{}'.format(user_id, album_name)
                    #file_directory_within_bucket = 'user_uploads/{}/'.format(album_name)

                    # synthesize a full file path; note that we included the filename
                    file_path_within_bucket = os.path.join(
                        file_directory_within_bucket,
                        file.name
                    )
                    custom_media_storage = CustomMediaStorage()
                    #custom_media_storage.bucket_name = AWS_STORAGE_BUCKET_NAME
                    custom_media_storage.save(file_path_within_bucket, file)
                    file_url = custom_media_storage.url(file_path_within_bucket)
                    file_name = file_url.split('/')[-1]
                    file_urls.append((file_name, file_url))
            else:
                fs = FileSystemStorage()
                fs.location = os.path.join(settings.MEDIA_ROOT , '/UploadedImages/')
                fs.save(file.name, file)

                #file_urls.append(upload.file.url)




        # try:
        #     logfile = temp_path+session_id+'/log.txt'
        #     with open(logfile,'w') as logfile:
        #         logfile.write("{} - Created log file\n".format(time.strftime("%x %X", time.gmtime())))
        #         logfile.write("Uploading files:\n")
        #         for f in filenames:
        #             logfile.write("{} - {}\n".format(time.strftime("%x %X", time.gmtime()), f))
        #         logfile.flush()
        #         logfile.close()
        #
        # except Exception as e:
        #     print('Error:',e)

        return render(request, 'OnlineImageConverter/upload_result.html', {
            'number_of_files': len(file_urls),
            'filenames': file_urls,
            'session_id':request.session._session_key,

        })
    else:
        return HttpResponse("No Files were uploaded")


def convert(request):
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        user_id = "none"

    number_of_files = int(request.GET.get('num'))
    s3 = boto3.resource('s3',
                        region_name="us-west-2",
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                        )
    bucket = s3.Bucket(AWS_MEDIA_BUCKET_NAME)
    bucket_prefix = 'user_uploads/{}/{}/'.format(user_id, "Uploads")
    url_prefix = 'https://django-media-public-1337.s3.amazonaws.com/'  # /user_uploads/1/Birthday2019/sky.jpg'
    image_list = []
    image_converter = ImageConverter()
    for obj in bucket.objects.filter(Prefix=bucket_prefix):
        source = str(url_prefix + obj.key)
        destination = source[:-4]+'_converted.jpg'
        file_name = destination.split('/')[-1]
        image_list.append((file_name, destination))

        # p = multiprocessing.Process(target=image_converter.convert_file,
        #                             args=(source, destination))
        # p.start()
        print('conversion start...')
        image_converter.convert_file(source)


    context = {
        'image_list': image_list,
        'number_of_files':number_of_files,
        'source': source,
        'destination':destination
    }

    #return redirect('/ConvertResult/?num=' + str(number_of_files))
    return render(request, 'OnlineImageConverter/convert_result.html', context)

def  convert_old(request):
    user_id=1
    session_id=1
    # organize a path for the file in bucket
    # file_directory_within_bucket = 'user_upload_files/{username}'.format(username=requests.user)
    album_name = 'Uploads'
    file_directory_within_bucket = '/user_uploads/{}/{}'.format(user_id, album_name)
    # file_directory_within_bucket = 'user_uploads/{}/'.format(album_name)


    number_of_files = int(request.GET.get('num'))
    source = temp_path + session_id + '/UploadedImages/'
    destination = temp_path + session_id + '/ConvertedImages/'
    image_converter = ImageConverter()
    failed_list = []

    def convert_files():

        counter = 1000
        for filename in os.listdir(source):
            converted_filename = 'IMG{}.jpg'.format(counter)
            try:
                logfile = temp_path + session_id + '/log.txt'
                with open(logfile, 'a') as logfile:
                    logfile.write(
                        "{0} - Converting {1} -> {2}\n".format(time.strftime("%x %X", time.gmtime()), filename,
                                                               converted_filename))
                    p = multiprocessing.Process(target=image_converter.convert_file,
                                                args=(source + filename, destination + converted_filename))
                    p.start()
                    # print("Starting Thread - waiting 15 secs.")
                    # Wait for 10 seconds or until process finishes
                    starting_time = time.time()
                    timeout_seconds = 15
                    while time.time() < (starting_time + timeout_seconds) and p.is_alive():
                        pass

                    if p.is_alive():  # if its still running after 30 Seconds terminate
                        print("{}Still running after 15 seconds...killing process...".format(filename))
                        logfile.write("{} - aborting conversion\n".format(time.strftime("%x %X", time.gmtime())))
                        failed_list.append(filename)
                        p.terminate()
                        p.join()
                    else:
                        logfile.write("{} - conversion successful\n".format(time.strftime("%x %X", time.gmtime())))
                        print("Regular Finish. Next file")
                    logfile.flush()
                    logfile.close()

            except Exception as e:
                print('Error: ', e)
            counter += 1
        with open(temp_path + session_id + '/log.txt', 'a') as logfile:
            logfile.write("{} - Conversion finished\n".format(time.strftime("%x %X", time.gmtime())))
            logfile.write("Total files attempted: {}\n".format(number_of_files))
            logfile.write("Successful conversions: {}\n".format(number_of_files - len(failed_list)))
            logfile.write("Failed conversions: {}\n".format(len(failed_list)))
            logfile.flush()
            logfile.close()
            print("Conversion finished")

    #conversion_process = multiprocessing.Process(target=convert_files)
    #conversion_process.start()

    return redirect('/OnlineImageConverter/ConvertResult/?session_id=' + session_id + '&num=' + str(number_of_files))


def convert_result(request):
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        user_id = "none"
    number_of_files = int(request.GET.get('num'))
    s3 = boto3.resource('s3',
                        region_name="us-west-2",
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                        )
    bucket = s3.Bucket(AWS_MEDIA_BUCKET_NAME)
    bucket_prefix = 'user_uploads/{}/{}/'.format(user_id, "Uploads")
    url_prefix = 'https://django-media-public-1337.s3.amazonaws.com/'  # /user_uploads/1/Birthday2019/sky.jpg'
    image_list = []
    for obj in bucket.objects.filter(Prefix=bucket_prefix):
        if obj.key.endswith("_converted.jpg"):
            image_url = url_prefix + obj.key
            image_name = image_url.split('/')[-1]
            image_list.append((image_name, image_url))

    return render(request, 'OnlineImageConverter/convert_result.html', {
        'number_of_files': number_of_files,
        'image_list': image_list
    })


    # cwd = os.getcwd()
    # session_id = request.GET.get('session_id')
    # number_of_files = int(request.GET.get('num'))
    # destination = temp_path + session_id + '/ConvertedImages/'
    # files = []
    # for file in os.listdir(destination):
    #     if file.endswith('-thumb.jpg'):
    #         pass
    #         #don't append thumbs
    #     else:
    #         files.append([file, file[:-4]+'-thumb.jpg'])
    # conversion_finished = (len(files) == number_of_files)

