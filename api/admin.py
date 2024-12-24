from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.CustomUser)
admin.site.register(models.ProfileRole)
admin.site.register(models.Profile)
admin.site.register(models.Department)
admin.site.register(models.Role)
admin.site.register(models.Gender)
