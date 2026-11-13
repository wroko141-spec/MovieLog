from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'MovieLog - администрирование'
admin.site.site_title = 'MovieLog'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('diary.urls')),
]

handler404 = 'diary.views.page_not_found'
