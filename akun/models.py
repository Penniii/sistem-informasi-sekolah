from django.contrib.auth.models import AbstractUser
from django.db import models

class Pengguna(AbstractUser):
    class Peran(models.TextChoices):
        TU = 'TU', 'Tata Usaha'
        GURU = 'GURU', 'Guru'
        SISWA = 'SISWA', 'Siswa'

    peran = models.CharField(
        max_length=10,
        choices=Peran.choices,
        default=Peran.SISWA,
    )

    wajib_ganti_password = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.peran = self.Peran.TU
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_peran_display()})'