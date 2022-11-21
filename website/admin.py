from django.contrib import admin

# Register your models here.
from .models import User, WishlistFile

admin.site.register(User)

class WishlistFileAdmin(admin.ModelAdmin):
    readonly_fields = ('uploaded_at',)

admin.site.register(WishlistFile,WishlistFileAdmin)



