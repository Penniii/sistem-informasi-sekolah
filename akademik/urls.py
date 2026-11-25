from django.urls import path

from . import views

urlpatterns = [
    path('siswa/', views.siswa_daftar, name='siswa_daftar'),
    path('siswa/tambah/', views.siswa_tambah, name='siswa_tambah'),
    path('siswa/<int:pk>/ubah/', views.siswa_ubah, name='siswa_ubah'),
    path('siswa/<int:pk>/hapus/', views.siswa_hapus, name='siswa_hapus'),
    path('siswa/<int:pk>/reset-password/', views.siswa_reset_password,
         name='siswa_reset_password'),

    path('guru/', views.guru_daftar, name='guru_daftar'),
    path('guru/tambah/', views.guru_tambah, name='guru_tambah'),
    path('guru/<int:pk>/ubah/', views.guru_ubah, name='guru_ubah'),
    path('guru/<int:pk>/hapus/', views.guru_hapus, name='guru_hapus'),
    path('guru/<int:pk>/reset-password/', views.guru_reset_password,
         name='guru_reset_password'),

    path('tahun-ajaran/', views.tahun_ajaran_daftar, name='tahun_ajaran_daftar'),
    path('tahun-ajaran/tambah/', views.tahun_ajaran_tambah, name='tahun_ajaran_tambah'),
    path('tahun-ajaran/<int:pk>/ubah/', views.tahun_ajaran_ubah, name='tahun_ajaran_ubah'),
    path('tahun-ajaran/<int:pk>/hapus/', views.tahun_ajaran_hapus, name='tahun_ajaran_hapus'),

    path('mapel/', views.mapel_daftar, name='mapel_daftar'),
    path('mapel/tambah/', views.mapel_tambah, name='mapel_tambah'),
    path('mapel/<int:pk>/ubah/', views.mapel_ubah, name='mapel_ubah'),
    path('mapel/<int:pk>/hapus/', views.mapel_hapus, name='mapel_hapus'),

    path('kelas/', views.kelas_daftar, name='kelas_daftar'),
    path('kelas/tambah/', views.kelas_tambah, name='kelas_tambah'),
    path('kelas/<int:pk>/', views.kelas_detail, name='kelas_detail'),
    path('kelas/<int:pk>/ubah/', views.kelas_ubah, name='kelas_ubah'),
    path('kelas/<int:pk>/hapus/', views.kelas_hapus, name='kelas_hapus'),

    path('jam-pelajaran/', views.jam_daftar, name='jam_daftar'),
    path('jam-pelajaran/tambah/', views.jam_tambah, name='jam_tambah'),
    path('jam-pelajaran/<int:pk>/ubah/', views.jam_ubah, name='jam_ubah'),
    path('jam-pelajaran/<int:pk>/hapus/', views.jam_hapus, name='jam_hapus'),

    path('jadwal/', views.jadwal_daftar, name='jadwal_daftar'),
    path('jadwal/tambah/', views.jadwal_tambah, name='jadwal_tambah'),
    path('jadwal/<int:pk>/ubah/', views.jadwal_ubah, name='jadwal_ubah'),
    path('jadwal/<int:pk>/hapus/', views.jadwal_hapus, name='jadwal_hapus'),

    path('jadwal-mengajar/', views.jadwal_guru, name='jadwal_guru'),
    path('jadwal-kelas/', views.jadwal_siswa, name='jadwal_siswa'),

    path('absensi/harian/', views.absensi_harian, name='absensi_harian'),
    path('absensi/rekap/', views.absensi_rekap, name='absensi_rekap'),

    path('absensi/pelajaran/', views.absensi_pelajaran, name='absensi_pelajaran'),
    path('absensi/pelajaran/<int:pk>/', views.absensi_pelajaran_isi, name='absensi_pelajaran_isi'),

    path('nilai/', views.nilai_daftar, name='nilai_daftar'),
    path('nilai/<int:kelas_id>/<int:mapel_id>/', views.nilai_isi, name='nilai_isi'),
    path('nilai-saya/', views.nilai_siswa, name='nilai_siswa'),

    path('leger/', views.leger, name='leger'),
    path('rapor/<int:siswa_id>/', views.rapor, name='rapor'),
]