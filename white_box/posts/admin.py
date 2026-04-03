from django.contrib import admin
from .models import PostContent, PostStats, Review, Favorite, Report
# Register your models here.
admin.site.register(PostContent)
admin.site.register(PostStats)
admin.site.register(Review)
admin.site.register(Favorite)
admin.site.register(Report)