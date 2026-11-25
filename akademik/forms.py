from django import forms

from django.core.exceptions import NON_FIELD_ERRORS

from .models import Guru, Jadwal, JamPelajaran, Kelas, MataPelajaran, Siswa, TahunAjaran

class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = ['nis', 'nama', 'jenis_kelamin', 'tanggal_lahir', 'kelas',
                  'nama_wali', 'no_hp_wali', 'no_hp', 'alamat']
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'alamat': forms.Textarea(attrs={'rows': 3}),
        }

class GuruForm(forms.ModelForm):
    class Meta:
        model = Guru
        fields = ['nip', 'nama', 'jenis_kelamin', 'tanggal_lahir', 'no_hp', 'alamat']
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'alamat': forms.Textarea(attrs={'rows': 3}),
        }

class TahunAjaranForm(forms.ModelForm):
    class Meta:
        model = TahunAjaran
        fields = ['nama', 'aktif', 'semester_aktif']
        help_texts = {
            'aktif': 'Hanya satu tahun ajaran yang bisa aktif. '
                     'Mengaktifkan yang ini otomatis menonaktifkan yang lain.',
        }


class MataPelajaranForm(forms.ModelForm):
    class Meta:
        model = MataPelajaran
        fields = ['kode', 'nama', 'kkm']
        
class KelasForm(forms.ModelForm):
    class Meta:
        model = Kelas
        fields = ['nama', 'tingkat', 'tahun_ajaran', 'wali_kelas']
        labels = {'wali_kelas': 'Wali kelas'}
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': 'Kelas dengan nama dan tahun ajaran ini sudah ada.',
            },
        }

class JamPelajaranForm(forms.ModelForm):
    class Meta:
        model = JamPelajaran
        fields = ['urutan', 'mulai', 'selesai']
        widgets = {
            'mulai': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'selesai': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }

class JadwalForm(forms.ModelForm):
    class Meta:
        model = Jadwal
        fields = ['kelas', 'hari', 'jam', 'mapel', 'guru']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': 'Kelas ini sudah punya pelajaran pada hari dan jam tersebut.',
            },
        }