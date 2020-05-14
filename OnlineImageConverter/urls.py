from django.urls import path, include

from . import views

urlpatterns = [
    path('' ,views.welcome, name='welcome'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('Upload/' ,views.upload, name='upload'),
    path('UploadResult/' ,views.upload_result, name='upload_result'),
    path('Convert/' ,views.convert, name='convert'),
    path('ConvertResult/' ,views.convert_result, name='convert_result'),
    path('start/', views.start, name='start'),
    path('album/', views.album, name='album'),
]