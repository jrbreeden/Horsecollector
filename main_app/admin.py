from django.contrib import admin

# Register your models here.
from .models import Horse, Feeding, Toy, Photo

admin.site.register(Horse)
admin.site.register(Feeding)
admin.site.register(Toy)
admin.site.register(Photo)