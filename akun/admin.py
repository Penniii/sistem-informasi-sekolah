from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Pengguna

@admin.register(Pengguna)
class PenggunaAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Peran', {'fields': ('peran',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Peran', {'fields': ('peran',)}),)
    list_filter = ('peran', 'is_active')