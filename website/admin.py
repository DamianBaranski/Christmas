from django.contrib import admin

# Register your models here.
from .models import User, WishlistFile, SiteSettings, DrawRun, DrawPair, Exclusion

admin.site.register(User)

class WishlistFileAdmin(admin.ModelAdmin):
    readonly_fields = ('uploaded_at',)

admin.site.register(WishlistFile,WishlistFileAdmin)




admin.site.register(SiteSettings)
admin.site.register(Exclusion)


class DrawPairInline(admin.TabularInline):
    model = DrawPair
    extra = 0


class DrawRunAdmin(admin.ModelAdmin):
    inlines = [DrawPairInline]


admin.site.register(DrawRun, DrawRunAdmin)
admin.site.site_header = 'List do Mikołaja – baza danych'
