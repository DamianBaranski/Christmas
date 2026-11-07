from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('website.urls')),
    path('admin/db/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]
# Uploaded letters are served by website.views.letter (/letters/<name>/)


