from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from test_center.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include ('accounts.urls')),
    path('', index ,name='home'),
    path("tests/<int:cluster_id>/", cluster_result, name="cluster_result"),
    path('clusters/', clusters_list, name='clusters_list'),
    path("tests/<int:cluster_id>/subjects/", subjects_list, name="subjects_list"),
    path("tests/<int:cluster_id>/<int:subject_id>/start/", start_test, name="start_test"),
    path("tests/<int:cluster_id>/<int:subject_id>/finish/", finish_test, name="finish_test"),
    path('tests/<int:cluster_id>/history/', attempts_history, name='attempts_history'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)