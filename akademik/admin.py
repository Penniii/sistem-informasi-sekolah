from django.contrib import admin

from .models import Guru, Kelas, MataPelajaran, Siswa, TahunAjaran


@admin.register(TahunAjaran)
class TahunAjaranAdmin(admin.ModelAdmin):
    list_display = ('nama', 'aktif')


@admin.register(MataPelajaran)
class MataPelajaranAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama')
    search_fields = ('kode', 'nama')


@admin.register(Guru)
class GuruAdmin(admin.ModelAdmin):
    list_display = ('nip', 'nama', 'jenis_kelamin', 'no_hp')
    search_fields = ('nip', 'nama')
    readonly_fields = ('pengguna',)


@admin.register(Kelas)
class KelasAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tingkat', 'tahun_ajaran', 'wali_kelas')
    list_filter = ('tahun_ajaran', 'tingkat')


@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = ('nis', 'nama', 'kelas', 'jenis_kelamin')
    list_filter = ('kelas',)
    search_fields = ('nis', 'nama')
    readonly_fields = ('pengguna',)