import datetime
from OnlineImageConverter.aws_backend import get_album_content, save_file_on_s3, FileUpload
from django.shortcuts import render, redirect
from django.http import HttpResponse
from OnlineImageConverter.models import Album

def welcome(request):
    return render(request, 'OnlineImageConverter/welcome.html')

def start(request):
    user_id = request.user.id if request.user.is_authenticated else 999
    albums = Album.objects.filter(album_user_id=user_id)

    context = {
        'user_id': user_id,
        'albums': albums
    }
    return render(request, 'OnlineImageConverter/start.html', context)


def create_album(request):

    user_id = request.user.id if request.user.is_authenticated else 999
    album_name = request.POST.get('album_name')

    #If Album Name was passed, create new Album
    if album_name:
        album = Album()
        album.album_name = album_name
        album.album_user_id = user_id
        album.album_date_created = datetime.date.today()
        album.save()
        album.album_s3_bucket_prefix = 'user_uploads/{}/{}/'.format(user_id, album.album_id)
        url_prefix = 'https://django-media-public-1337.s3.amazonaws.com/'
        album.album_url = url_prefix + album.album_s3_bucket_prefix
        album.save()


        return redirect('/album/'+ str(album.album_id))
        #return render(request, 'OnlineImageConverter/album.html', {"album": album})
    else:
        return HttpResponse("You did not specify an album name")

def album(request, album_id, fileupload=None):
#This is the view function for the /album/ URL
#It checks if the user has access to the requested album and retrieves the content
    user_id = request.user.id if request.user.is_authenticated else 999
    album = Album.objects.get(album_id=album_id)
    if user_id == album.album_user_id:
        #Display Album Content
        file_list = get_album_content(album)
        return render(request, 'OnlineImageConverter/album.html', {'fileupload':fileupload,  \
                                                                   'album':album, 'file_list':file_list})
    else:
        return render(request, 'OnlineImageConverter/error.html', {'error':'You don\'t have access to this page'})


def upload(request, album_id):
    fileupload = FileUpload()
    fileupload.album = Album.objects.get(album_id=album_id)
    fileupload.file_list = request.FILES.getlist('file_uploads')
    fileupload.num_files = len(fileupload.file_list)
    if request.user.is_authenticated:
        for file in fileupload.file_list:
             save_file_on_s3(file, fileupload.album)
    else:
        file = fileupload.file_list[0]
        if file.size < 1_000_000:
            save_file_on_s3(file, fileupload.album)
        else:
            fileupload.error = 'The file was too big. As guest user the file size is limited to 1 MB.'
    # return render(request, 'OnlineImageConverter/upload_result.html', {'album':album_obj, 'file_list':file_list})
    return album(request, album_id, fileupload=fileupload)