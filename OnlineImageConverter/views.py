import os
import boto3

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from OnlineImageConverter.storage_backends import CustomMediaStorage
from OnlineImageConverter.models import ImageConverter, ImageUpload
from DjangoProject.settings import BASE_DIR, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_MEDIA_BUCKET_NAME
import multiprocessing
import time

temp_path = BASE_DIR + '/OnlineImageConverter/static/OnlineImageConverter/temp/'

def index(request):
    return HttpResponse("Index")


def welcome(request):

    return render(request, 'OnlineImageConverter/welcome.html')

def start(request):
    user_id=request.user.id

    #Get list of Albumsfor this user
    s3 = boto3.resource('s3',
                        region_name="us-west-2",
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                        )
    # S3 list all keys with the prefix 'photos/'
    keys=set()
    s3 = boto3.resource('s3')
    #bucket = s3.Bucket('django-media-public-1337')
    bucket = s3.Bucket(AWS_MEDIA_BUCKET_NAME)
    bucket_prefix = 'user_uploads/{}/'.format(user_id)
    for obj in bucket.objects.filter(Prefix=bucket_prefix):
        keys.add(obj.key.split('/')[2])

    context = {
        'user_id':user_id,
        'keys':keys
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

    session_items = request.session.keys()
    user_id = request.user.id
    session_key = request.session._get_or_create_session_key()

    #if request.user.is_authenticated:
    return render(request, 'OnlineImageConverter/upload.html', {'user_id': user_id,
                                                                    'session_items': session_items,
                                                                    'session_key': session_key,
                                                                    'env': os.getenv('AWS_STORAGE_BUCKET_NAME')})
    # else:
    #     return HttpResponse("Please log in")



def upload_result(request):
    if request.method == 'POST' and len(request.FILES.getlist('file_uploads'))>0:
        user_id = request.user.id

        file_urls = []
        for file in request.FILES.getlist('file_uploads'):
            if settings.USE_S3:
                s3 = boto3.resource('s3',
                                    region_name="us-west-2",
                                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                                    )
                #organize a path for the file in bucket
                #file_directory_within_bucket = 'user_upload_files/{username}'.format(username=requests.user)
                album_name = 'Birthday2019'
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
                file_urls.append(file_url)
            else:
                fs = FileSystemStorage()
                fs.location = temp_path + '/UploadedImages/'
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
            # 'session_id':session_id,
            'session_id':request.session._session_key,

        })
    else:
        return HttpResponse("No Files were uploaded")

@login_required
def convert(request):
    session_id = request.GET.get(key='session_id')
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

@login_required
def convert_result(request):
    cwd = os.getcwd()
    session_id = request.GET.get('session_id')
    number_of_files = int(request.GET.get('num'))
    destination = temp_path + session_id + '/ConvertedImages/'
    files = []
    for file in os.listdir(destination):
        if file.endswith('-thumb.jpg'):
            pass
            #don't append thumbs
        else:
            files.append([file, file[:-4]+'-thumb.jpg'])
    conversion_finished = (len(files) == number_of_files)
    return render(request, 'OnlineImageConverter/convert_result.html', {
        'number_of_files':number_of_files,
        'files':files,
        'cwd':cwd,
        'conversion_finished': conversion_finished,
        'file_url': '/static/OnlineImageConverter/temp/'+session_id+'/ConvertedImages/',
    })
