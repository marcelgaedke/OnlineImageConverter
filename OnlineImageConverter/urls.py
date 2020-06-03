from django.urls import path, include
from django.conf.urls import url

from . import views

urlpatterns = [
    path('' ,views.welcome, name='welcome'),
    path('accounts/', include('django.contrib.auth.urls')),
    #path(r'^upload/([0-9]{4})/$' ,views.upload, name='upload'),
    url(r'^upload/(?P<album_id>(\d+))/$', views.upload, name='upload'),
    url(r'^album/(?P<album_id>(\d+))/$', views.album, name='album'),
    #path('UploadResult/' ,views.upload_result, name='upload_result'),
    #path('Convert/' ,views.convert, name='convert'),
    #path('ConvertResult/' ,views.convert_result, name='convert_result'),
    path('start/', views.start, name='start'),
    #path('album/', views.album, name='album'),
    path('create_album/', views.create_album, name='create_album'),
]