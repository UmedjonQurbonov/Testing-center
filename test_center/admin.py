from django.contrib import admin
from .models import Cluster, Subject, Question, Answer

admin.site.register(Cluster)
admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(Answer)
