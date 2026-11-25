from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

from django.core.exceptions import ValidationError
from django.db import models, transaction

from akun.models import Pengguna

class Semester(models.TextChoices):
    GANJIL = '1', 'Ganjil'
    GENAP = '2', 'Genap'


class TahunAjaran(models.Model):
    nama = models.CharField('Tahun ajaran', max_length=9, unique=True,
                            help_text='Contoh: 2025/2026')
    aktif = models.BooleanField(default=False)
    semester_aktif = models.CharField(
        'Semester aktif', max_length=1, choices=Semester.choices,
        default=Semester.GANJIL,
    )

    class Meta:
        ordering = ['-nama']
        verbose_name = 'Tahun ajaran'
        verbose_name_plural = 'Tahun ajaran'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.aktif:
            TahunAjaran.objects.exclude(pk=self.pk).update(aktif=False)

    def __str__(self):
        return self.nama


class MataPelajaran(models.Model):
    kode = models.CharField(max_length=10, unique=True)
    nama = models.CharField('Nama mata pelajaran', max_length=100)
    kkm = models.PositiveSmallIntegerField(
        'KKM', default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Nilai minimum untuk dinyatakan tuntas.',
    )

    class Meta:
        ordering = ['nama']
        verbose_name = 'Mata pelajaran'
        verbose_name_plural = 'Mata pelajaran'

    def __str__(self):
        return self.nama


class ProfilDasar(models.Model):
    """Kerangka bersama untuk Guru dan Siswa (tidak jadi tabel sendiri)."""

    class JenisKelamin(models.TextChoices):
        LAKI = 'L', 'Laki-laki'
        PEREMPUAN = 'P', 'Perempuan'

    PERAN = None  # diisi oleh Guru dan Siswa

    pengguna = models.OneToOneField(
        Pengguna, on_delete=models.PROTECT, null=True, blank=True,
        editable=False, related_name='%(class)s',
    )
    nama = models.CharField('Nama lengkap', max_length=150)
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices)
    tanggal_lahir = models.DateField()
    no_hp = models.CharField('No. HP', max_length=20, blank=True)
    alamat = models.TextField(blank=True)

    class Meta:
        abstract = True

    def username_akun(self):
        raise NotImplementedError

    def password_awal(self):
        return self.tanggal_lahir.strftime('%d%m%Y')

    def _buat_akun(self):
        akun = Pengguna(
            username=self.username_akun(),
            first_name=self.nama,
            peran=self.PERAN,
            wajib_ganti_password=True,
        )
        akun.set_password(self.password_awal())
        akun.save()
        return akun

    def reset_password(self):
        self.pengguna.set_password(self.password_awal())
        self.pengguna.wajib_ganti_password = True
        self.pengguna.save()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pengguna_id is None:
                self.pengguna = self._buat_akun()
            else:
                akun = self.pengguna
                akun.first_name = self.nama
                akun.username = self.username_akun()
                akun.save()
            super().save(*args, **kwargs)

class Guru(ProfilDasar):
    PERAN = Pengguna.Peran.GURU

    nip = models.CharField('NIP / ID Guru', max_length=30, unique=True)

    class Meta:
        ordering = ['nama']
        verbose_name_plural = 'Guru'

    def username_akun(self):
        return self.nip

    def __str__(self):
        return self.nama


class Kelas(models.Model):
    class Tingkat(models.IntegerChoices):
        TUJUH = 7, 'Kelas 7'
        DELAPAN = 8, 'Kelas 8'
        SEMBILAN = 9, 'Kelas 9'

    nama = models.CharField(max_length=10, help_text='Contoh: 7A')
    tingkat = models.IntegerField(choices=Tingkat.choices)
    tahun_ajaran = models.ForeignKey(TahunAjaran, on_delete=models.PROTECT)
    wali_kelas = models.ForeignKey(Guru, on_delete=models.SET_NULL,
                                   null=True, blank=True)

    class Meta:
        ordering = ['tahun_ajaran', 'nama']
        verbose_name_plural = 'Kelas'
        constraints = [
            models.UniqueConstraint(fields=['nama', 'tahun_ajaran'],
                                    name='kelas_unik_per_tahun'),
        ]

    def __str__(self):
        return f'{self.nama} ({self.tahun_ajaran})'


class Siswa(ProfilDasar):
    PERAN = Pengguna.Peran.SISWA

    nis = models.CharField('NIS', max_length=20, unique=True)
    kelas = models.ForeignKey(Kelas, on_delete=models.SET_NULL,
                              null=True, blank=True)
    nama_wali = models.CharField('Nama orang tua / wali', max_length=150, blank=True)
    no_hp_wali = models.CharField('No. HP orang tua / wali', max_length=20, blank=True)

    class Meta:
        ordering = ['nama']
        verbose_name_plural = 'Siswa'

    def username_akun(self):
        return self.nis

    def __str__(self):
        return f'{self.nama} ({self.nis})'

class JamPelajaran(models.Model):
    urutan = models.PositiveSmallIntegerField('Jam ke', unique=True)
    mulai = models.TimeField('Jam mulai')
    selesai = models.TimeField('Jam selesai')

    class Meta:
        ordering = ['urutan']
        verbose_name = 'Jam pelajaran'
        verbose_name_plural = 'Jam pelajaran'

    def clean(self):
        if self.mulai and self.selesai and self.selesai <= self.mulai:
            raise ValidationError('Jam selesai harus lebih akhir dari jam mulai.')

    def __str__(self):
        return f'Jam ke-{self.urutan} ({self.mulai:%H:%M}–{self.selesai:%H:%M})'

class Jadwal(models.Model):
    class Hari(models.IntegerChoices):
        SENIN = 1, 'Senin'
        SELASA = 2, 'Selasa'
        RABU = 3, 'Rabu'
        KAMIS = 4, 'Kamis'
        JUMAT = 5, 'Jumat'
        SABTU = 6, 'Sabtu'

    kelas = models.ForeignKey(Kelas, on_delete=models.PROTECT)
    hari = models.PositiveSmallIntegerField(choices=Hari.choices)
    jam = models.ForeignKey(JamPelajaran, on_delete=models.PROTECT)
    mapel = models.ForeignKey(MataPelajaran, on_delete=models.PROTECT,
                              verbose_name='Mata pelajaran')
    guru = models.ForeignKey(Guru, on_delete=models.PROTECT)

    class Meta:
        ordering = ['hari', 'jam__urutan']
        verbose_name_plural = 'Jadwal'
        constraints = [
            models.UniqueConstraint(fields=['kelas', 'hari', 'jam'],
                                    name='jadwal_unik_kelas_hari_jam'),
        ]

    def clean(self):
        if not (self.kelas_id and self.jam_id and self.guru_id and self.hari):
            return
        bentrok = Jadwal.objects.filter(
            guru_id=self.guru_id,
            hari=self.hari,
            jam_id=self.jam_id,
            kelas__tahun_ajaran_id=self.kelas.tahun_ajaran_id,
        ).exclude(pk=self.pk).select_related('kelas').first()
        if bentrok:
            raise ValidationError(
                f'{self.guru} sudah mengajar di kelas {bentrok.kelas.nama} '
                f'pada hari dan jam yang sama.'
            )

    def __str__(self):
        return (f'{self.kelas.nama} {self.get_hari_display()} '
                f'jam ke-{self.jam.urutan}: {self.mapel}')

class AbsensiHarian(models.Model):
    class Status(models.TextChoices):
        HADIR = 'HADIR', 'Hadir'
        SAKIT = 'SAKIT', 'Sakit'
        IZIN = 'IZIN', 'Izin'
        ALPA = 'ALPA', 'Alpa'

    tanggal = models.DateField()
    kelas = models.ForeignKey(Kelas, on_delete=models.PROTECT)
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    status = models.CharField(max_length=5, choices=Status.choices,
                              default=Status.HADIR)
    keterangan = models.CharField(max_length=200, blank=True)
    dicatat_oleh = models.ForeignKey(Pengguna, on_delete=models.SET_NULL,
                                     null=True, blank=True, editable=False)
    diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-tanggal', 'siswa__nama']
        verbose_name = 'Absensi harian'
        verbose_name_plural = 'Absensi harian'
        constraints = [
            models.UniqueConstraint(fields=['siswa', 'tanggal'],
                                    name='absensi_harian_unik_siswa_tanggal'),
        ]

    def __str__(self):
        return f'{self.siswa.nama} {self.tanggal:%d/%m/%Y}: {self.get_status_display()}'

class AbsensiPelajaran(models.Model):
    tanggal = models.DateField()
    jadwal = models.ForeignKey(Jadwal, on_delete=models.PROTECT)
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    status = models.CharField(max_length=5, choices=AbsensiHarian.Status.choices,
                              default=AbsensiHarian.Status.HADIR)
    keterangan = models.CharField(max_length=200, blank=True)
    dicatat_oleh = models.ForeignKey(Pengguna, on_delete=models.SET_NULL,
                                     null=True, blank=True, editable=False)
    diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-tanggal', 'jadwal__jam__urutan', 'siswa__nama']
        verbose_name = 'Absensi pelajaran'
        verbose_name_plural = 'Absensi pelajaran'
        constraints = [
            models.UniqueConstraint(fields=['jadwal', 'siswa', 'tanggal'],
                                    name='absensi_pelajaran_unik'),
        ]

    def __str__(self):
        return f'{self.siswa.nama} {self.tanggal:%d/%m/%Y}: {self.get_status_display()}'

class Nilai(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    mapel = models.ForeignKey(MataPelajaran, on_delete=models.PROTECT)
    kelas = models.ForeignKey(Kelas, on_delete=models.PROTECT)
    semester = models.CharField(max_length=1, choices=Semester.choices)
    tugas = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    uts = models.DecimalField(
        'UTS', max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    uas = models.DecimalField(
        'UAS', max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    nilai_akhir = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, editable=False,
    )
    dicatat_oleh = models.ForeignKey(Pengguna, on_delete=models.SET_NULL,
                                     null=True, blank=True, editable=False)
    diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['mapel__nama']
        verbose_name_plural = 'Nilai'
        constraints = [
            models.UniqueConstraint(fields=['siswa', 'mapel', 'kelas', 'semester'],
                                    name='nilai_unik'),
        ]

    def hitung_akhir(self):
        if self.tugas is None or self.uts is None or self.uas is None:
            return None
        bobot = settings.BOBOT_NILAI
        total = (
            self.tugas * bobot['tugas']
            + self.uts * bobot['uts']
            + self.uas * bobot['uas']
        ) / Decimal(100)
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.nilai_akhir = self.hitung_akhir()
        super().save(*args, **kwargs)

    @property
    def predikat(self):
        n = self.nilai_akhir
        if n is None:
            return ''
        if n >= 90:
            return 'A'
        if n >= 80:
            return 'B'
        if n >= 70:
            return 'C'
        return 'D'

    @property
    def tuntas(self):
        return self.nilai_akhir is not None and self.nilai_akhir >= self.mapel.kkm

    def __str__(self):
        return f'{self.siswa.nama} {self.mapel.nama} semester {self.get_semester_display()}'