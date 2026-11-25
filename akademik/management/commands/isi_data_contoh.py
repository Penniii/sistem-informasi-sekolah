"""Perintah: python manage.py isi_data_contoh

Mengisi database dengan data contoh yang realistis untuk demo dan portfolio.
"""
import datetime
import random
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from akademik.models import (
    AbsensiHarian, AbsensiPelajaran, Guru, Jadwal, JamPelajaran, Kelas,
    MataPelajaran, Nilai, Semester, Siswa, TahunAjaran,
)
from akun.models import Pengguna

SANDI_DEMO = 'demo12345'

MAPEL = [
    ('MTK', 'Matematika'), ('BIN', 'Bahasa Indonesia'), ('BIG', 'Bahasa Inggris'),
    ('IPA', 'Ilmu Pengetahuan Alam (IPA)'), ('IPS', 'Ilmu Pengetahuan Sosial (IPS)'),
    ('PKN', 'Pendidikan Pancasila'), ('SBK', 'Seni Budaya'), ('PJK', 'PJOK'),
    ('INF', 'Informatika'),
]

GURU = [
    ('Budi Santoso, S.Pd.', 'L'), ('Siti Rahmawati, S.Pd.', 'P'),
    ('Agus Pratama, S.Pd.', 'L'), ('Dewi Lestari, S.Si.', 'P'),
    ('Hendra Wijaya, S.Pd.', 'L'), ('Rina Kusuma, S.Pd.', 'P'),
    ('Joko Susilo, S.Sn.', 'L'), ('Eko Prasetyo, S.Pd.', 'L'),
    ('Maya Anggraini, S.Kom.', 'P'),
]

KELAS = [('7A', 7), ('7B', 7), ('8A', 8), ('8B', 8), ('9A', 9), ('9B', 9)]

JAM = [
    (1, '07:00', '07:40'), (2, '07:40', '08:20'), (3, '08:20', '09:00'),
    (4, '09:15', '09:55'), (5, '09:55', '10:35'), (6, '10:35', '11:15'),
]

NAMA_L = ['Ahmad', 'Budi', 'Cahyo', 'Dimas', 'Eko', 'Fajar', 'Galih', 'Hadi', 'Irfan',
          'Joko', 'Krisna', 'Lukman', 'Maulana', 'Nanda', 'Oki', 'Putra', 'Rangga',
          'Satria', 'Tegar', 'Wahyu']
NAMA_P = ['Anisa', 'Bunga', 'Citra', 'Dian', 'Eka', 'Fitri', 'Gita', 'Hana', 'Indah',
          'Jihan', 'Kartika', 'Lestari', 'Maya', 'Nadia', 'Olivia', 'Putri', 'Rani',
          'Salsa', 'Tiara', 'Wulan']
NAMA_BELAKANG = ['Pratama', 'Saputra', 'Wijaya', 'Kusuma', 'Santoso', 'Hidayat', 'Permata',
                 'Nugroho', 'Ramadhan', 'Setiawan', 'Maharani', 'Firmansyah', 'Anggraini',
                 'Syahputra', 'Puspita', 'Rahayu']

STATUS = ['HADIR', 'SAKIT', 'IZIN', 'ALPA']
BOBOT_STATUS = [92, 3, 3, 2]


def skor(acak, kemampuan):
    """Satu angka nilai 35-100 di sekitar kemampuan siswa."""
    return Decimal(max(35, min(100, round(acak.gauss(78 + kemampuan, 8)))))


class Command(BaseCommand):
    help = 'Mengisi database dengan data contoh: guru, siswa, kelas, jadwal, absensi, dan nilai.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Hapus dulu semua data akademik dan akun non-superuser.',
        )
        parser.add_argument(
            '--seed', type=int, default=2025,
            help='Angka acak awal. Seed yang sama menghasilkan data yang sama.',
        )

    def handle(self, *args, **opsi):
        if opsi['reset']:
            jawaban = input(
                'Semua data akademik dan akun non-superuser akan DIHAPUS. '
                'Ketik YA untuk lanjut: '
            )
            if jawaban.strip() != 'YA':
                raise CommandError('Dibatalkan.')
            self._hapus_data()
        elif Siswa.objects.exists() or Guru.objects.exists():
            raise CommandError(
                'Database sudah berisi data guru atau siswa. '
                'Gunakan database kosong, atau tambahkan --reset.'
            )

        acak = random.Random(opsi['seed'])
        with transaction.atomic():
            ringkasan = self._isi(acak)

        self.stdout.write(self.style.SUCCESS('Data contoh berhasil dibuat.'))
        for baris in ringkasan['jumlah']:
            self.stdout.write(f'  {baris}')
        self.stdout.write('')
        self.stdout.write(f'Akun contoh (sandi semuanya: {SANDI_DEMO}):')
        self.stdout.write(f"  TU    : {ringkasan['tu']}")
        self.stdout.write(f"  Guru  : {ringkasan['guru']}")
        self.stdout.write(f"  Siswa : {ringkasan['siswa']}")

    def _hapus_data(self):
        for model in (Nilai, AbsensiPelajaran, AbsensiHarian, Jadwal, Siswa, Guru,
                      Kelas, JamPelajaran, MataPelajaran, TahunAjaran):
            model.objects.all().delete()
        Pengguna.objects.filter(is_superuser=False).delete()

    def _isi(self, acak):
        hari_ini = timezone.localdate()
        if hari_ini.month >= 7:
            awal, semester = hari_ini.year, Semester.GANJIL
        else:
            awal, semester = hari_ini.year - 1, Semester.GENAP

        # Sandi demo di-hash SEKALI lalu dipakai semua akun. Meng-hash 150 sandi
        # satu per satu lewat form biasa akan memakan waktu lebih dari satu menit.
        sandi = make_password(SANDI_DEMO)

        # --- Data master ---
        tahun, _ = TahunAjaran.objects.get_or_create(nama=f'{awal}/{awal + 1}')
        tahun.aktif = True
        tahun.semester_aktif = semester
        tahun.save()

        daftar_mapel = [
            MataPelajaran.objects.get_or_create(kode=kode, defaults={'nama': nama})[0]
            for kode, nama in MAPEL
        ]
        daftar_jam = [
            JamPelajaran.objects.get_or_create(
                urutan=urutan,
                defaults={
                    'mulai': datetime.time.fromisoformat(mulai),
                    'selesai': datetime.time.fromisoformat(selesai),
                },
            )[0]
            for urutan, mulai, selesai in JAM
        ]

        # --- Akun TU contoh ---
        tu, _ = Pengguna.objects.get_or_create(
            username='tu.demo',
            defaults={
                'first_name': 'Tata Usaha',
                'peran': Pengguna.Peran.TU,
                'password': sandi,
            },
        )

        # --- Guru: satu guru untuk tiap mata pelajaran ---
        daftar_guru = []
        for nomor, (nama, jk) in enumerate(GURU, start=1):
            nip = f'19{70 + nomor}0615201001{nomor:04d}'
            akun = Pengguna.objects.create(
                username=nip, first_name=nama,
                peran=Pengguna.Peran.GURU, password=sandi,
            )
            daftar_guru.append(Guru.objects.create(
                pengguna=akun, nip=nip, nama=nama, jenis_kelamin=jk,
                tanggal_lahir=datetime.date(1970 + nomor, 6, 15),
                no_hp=f'0812000{nomor:04d}',
                alamat=f'Jl. Pendidikan No. {nomor}',
            ))

        # --- Kelas: wali kelas diambil dari 6 guru pertama ---
        daftar_kelas = []
        for urutan, (nama, tingkat) in enumerate(KELAS):
            kelas, _ = Kelas.objects.get_or_create(
                nama=nama, tahun_ajaran=tahun, defaults={'tingkat': tingkat},
            )
            kelas.tingkat = tingkat
            kelas.wali_kelas = daftar_guru[urutan]
            kelas.save()
            daftar_kelas.append(kelas)

        # --- Siswa: 24 per kelas ---
        daftar_siswa = []
        for urutan, kelas in enumerate(daftar_kelas):
            for nomor in range(1, 25):
                jk = 'L' if nomor % 2 else 'P'
                nama = (f"{acak.choice(NAMA_L if jk == 'L' else NAMA_P)} "
                        f"{acak.choice(NAMA_BELAKANG)}")
                nis = f'{awal}{urutan + 1:02d}{nomor:02d}'
                akun = Pengguna.objects.create(
                    username=nis, first_name=nama,
                    peran=Pengguna.Peran.SISWA, password=sandi,
                )
                daftar_siswa.append(Siswa.objects.create(
                    pengguna=akun, nis=nis, nama=nama, jenis_kelamin=jk,
                    tanggal_lahir=datetime.date(
                        awal - 12 - (kelas.tingkat - 7),
                        acak.randint(1, 12), acak.randint(1, 28),
                    ),
                    kelas=kelas,
                    nama_wali=f"Bapak/Ibu {nama.split()[-1]}",
                    no_hp_wali=f'0813{acak.randint(1000000, 9999999)}',
                    alamat=f'Jl. Melati No. {acak.randint(1, 99)}',
                ))

        # --- Jadwal: Senin-Jumat, tanpa bentrok ---
        # Pada satu hari dan jam yang sama, tiap kelas mendapat mapel yang berbeda,
        # dan tiap mapel punya satu guru, jadi tidak ada guru yang mengajar di dua tempat.
        daftar_jadwal = []
        for urutan, kelas in enumerate(daftar_kelas):
            for hari in range(1, 6):
                for nomor_jam, jam in enumerate(daftar_jam):
                    m = (urutan + hari * 2 + nomor_jam) % len(daftar_mapel)
                    daftar_jadwal.append(Jadwal(
                        kelas=kelas, hari=hari, jam=jam,
                        mapel=daftar_mapel[m], guru=daftar_guru[m],
                    ))
        Jadwal.objects.bulk_create(daftar_jadwal)

        # --- Absensi harian: 20 hari kerja terakhir ---
        hari_kerja = []
        tanggal = hari_ini
        while len(hari_kerja) < 20:
            if tanggal.weekday() < 5:
                hari_kerja.append(tanggal)
            tanggal -= datetime.timedelta(days=1)

        absensi = []
        for siswa in daftar_siswa:
            for tanggal in hari_kerja:
                status = acak.choices(STATUS, weights=BOBOT_STATUS)[0]
                absensi.append(AbsensiHarian(
                    tanggal=tanggal, kelas=siswa.kelas, siswa=siswa, status=status,
                    keterangan='Demam' if status == 'SAKIT' else '',
                ))
        AbsensiHarian.objects.bulk_create(absensi)

        # --- Nilai: semua mapel, semester berjalan ---
        daftar_nilai = []
        for siswa in daftar_siswa:
            kemampuan = acak.gauss(0, 7)
            for mapel in daftar_mapel:
                nilai = Nilai(
                    siswa=siswa, mapel=mapel, kelas=siswa.kelas, semester=semester,
                    tugas=skor(acak, kemampuan),
                    uts=skor(acak, kemampuan),
                    uas=skor(acak, kemampuan) if acak.random() > 0.03 else None,
                )
                nilai.nilai_akhir = nilai.hitung_akhir()
                daftar_nilai.append(nilai)
        Nilai.objects.bulk_create(daftar_nilai)

        return {
            'jumlah': [
                f'Tahun ajaran     : {tahun.nama} (semester {Semester(semester).label})',
                f'Mata pelajaran   : {len(daftar_mapel)}',
                f'Guru             : {len(daftar_guru)}',
                f'Kelas            : {len(daftar_kelas)}',
                f'Siswa            : {len(daftar_siswa)}',
                f'Jadwal           : {len(daftar_jadwal)}',
                f'Absensi harian   : {len(absensi)}',
                f'Nilai            : {len(daftar_nilai)}',
            ],
            'tu': tu.username,
            'guru': f'{daftar_guru[0].nip}  ({daftar_guru[0].nama}, wali kelas 7A)',
            'siswa': f'{daftar_siswa[0].nis}  ({daftar_siswa[0].nama}, kelas 7A)',
        }