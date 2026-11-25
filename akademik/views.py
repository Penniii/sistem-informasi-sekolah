import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, ProtectedError, Q
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from akun.decorators import peran_diperlukan

from .forms import (
    GuruForm, JadwalForm, JamPelajaranForm, KelasForm, MataPelajaranForm,
    SiswaForm, TahunAjaranForm,
)

from .models import (
    AbsensiHarian, AbsensiPelajaran, Guru, Jadwal, JamPelajaran, Kelas,
    MataPelajaran, Nilai, Semester, Siswa, TahunAjaran,
)

@peran_diperlukan('TU')
def siswa_daftar(request):
    siswa = Siswa.objects.select_related('kelas', 'kelas__tahun_ajaran')

    kata_kunci = request.GET.get('q', '').strip()
    kelas_id = request.GET.get('kelas', '')

    if kata_kunci:
        siswa = siswa.filter(Q(nama__icontains=kata_kunci) | Q(nis__icontains=kata_kunci))
    if kelas_id:
        siswa = siswa.filter(kelas_id=kelas_id)

    halaman = Paginator(siswa, 20).get_page(request.GET.get('halaman'))

    return render(request, 'akademik/siswa_daftar.html', {
        'halaman': halaman,
        'kata_kunci': kata_kunci,
        'kelas_id': kelas_id,
        'daftar_kelas': Kelas.objects.select_related('tahun_ajaran'),
    })


@peran_diperlukan('TU')
def siswa_tambah(request):
    form = SiswaForm(request.POST or None)
    if form.is_valid():
        siswa = form.save()
        messages.success(
            request,
            f'Siswa {siswa.nama} ditambahkan. Akun login: {siswa.nis}, '
            f'password awal: tanggal lahir (DDMMYYYY).',
        )
        return redirect('siswa_daftar')
    return render(request, 'akademik/siswa_form.html',
                  {'form': form, 'judul': 'Tambah Siswa'})


@peran_diperlukan('TU')
def siswa_ubah(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    form = SiswaForm(request.POST or None, instance=siswa)
    if form.is_valid():
        form.save()
        messages.success(request, f'Data {siswa.nama} berhasil diperbarui.')
        return redirect('siswa_daftar')
    return render(request, 'akademik/siswa_form.html',
                  {'form': form, 'judul': 'Ubah Siswa', 'siswa': siswa})


@peran_diperlukan('TU')
def siswa_hapus(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            akun = siswa.pengguna
            siswa.delete()
            if akun:
                akun.delete()
        messages.success(request, f'Siswa {siswa.nama} dan akun loginnya telah dihapus.')
        return redirect('siswa_daftar')
    return render(request, 'akademik/siswa_hapus.html', {'siswa': siswa})


@peran_diperlukan('TU')
def siswa_reset_password(request, pk):
    siswa = get_object_or_404(Siswa, pk=pk)
    if request.method == 'POST':
        siswa.reset_password()
        messages.success(
            request,
            f'Password {siswa.nama} dikembalikan ke tanggal lahir (DDMMYYYY).',
        )
    return redirect('siswa_daftar')

@peran_diperlukan('TU')
def guru_daftar(request):
    guru = Guru.objects.all()

    kata_kunci = request.GET.get('q', '').strip()
    if kata_kunci:
        guru = guru.filter(Q(nama__icontains=kata_kunci) | Q(nip__icontains=kata_kunci))

    halaman = Paginator(guru, 20).get_page(request.GET.get('halaman'))

    return render(request, 'akademik/guru_daftar.html', {
        'halaman': halaman,
        'kata_kunci': kata_kunci,
    })


@peran_diperlukan('TU')
def guru_tambah(request):
    form = GuruForm(request.POST or None)
    if form.is_valid():
        guru = form.save()
        messages.success(
            request,
            f'Guru {guru.nama} ditambahkan. Akun login: {guru.nip}, '
            f'password awal: tanggal lahir (DDMMYYYY).',
        )
        return redirect('guru_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Tambah Guru',
        'kembali': 'guru_daftar',
        'info': 'Akun login guru dibuat otomatis: username berupa NIP / ID Guru, '
                'password awal berupa tanggal lahir (DDMMYYYY). '
                'Guru wajib menggantinya saat pertama login.',
    })


@peran_diperlukan('TU')
def guru_ubah(request, pk):
    guru = get_object_or_404(Guru, pk=pk)
    form = GuruForm(request.POST or None, instance=guru)
    if form.is_valid():
        form.save()
        messages.success(request, f'Data {guru.nama} berhasil diperbarui.')
        return redirect('guru_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Ubah Guru',
        'kembali': 'guru_daftar',
        'info': 'Mengubah tanggal lahir tidak mengubah password guru. '
                'Klik Reset password di daftar guru bila password perlu disamakan.',
    })


@peran_diperlukan('TU')
def guru_hapus(request, pk):
    guru = get_object_or_404(Guru, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                akun = guru.pengguna
                guru.delete()
                if akun:
                    akun.delete()
        except ProtectedError:
            messages.error(
                request,
                f'Guru {guru.nama} tidak bisa dihapus karena masih tercatat mengajar di jadwal.',
            )
        else:
            messages.success(request, f'Guru {guru.nama} dan akun loginnya telah dihapus.')
        return redirect('guru_daftar')
    return render(request, 'akademik/hapus_umum.html', {
        'judul': 'Hapus guru?',
        'nama_objek': f'{guru.nama} (NIP {guru.nip})',
        'keterangan': 'beserta akun loginnya',
        'kembali': 'guru_daftar',
    })

@peran_diperlukan('TU')
def guru_reset_password(request, pk):
    guru = get_object_or_404(Guru, pk=pk)
    if request.method == 'POST':
        guru.reset_password()
        messages.success(
            request,
            f'Password {guru.nama} dikembalikan ke tanggal lahir (DDMMYYYY).',
        )
    return redirect('guru_daftar')

# ===== Tahun Ajaran =====

@peran_diperlukan('TU')
def tahun_ajaran_daftar(request):
    return render(request, 'akademik/tahun_ajaran_daftar.html', {
        'daftar': TahunAjaran.objects.all(),
    })


@peran_diperlukan('TU')
def tahun_ajaran_tambah(request):
    form = TahunAjaranForm(request.POST or None)
    if form.is_valid():
        tahun = form.save()
        messages.success(request, f'Tahun ajaran {tahun.nama} ditambahkan.')
        return redirect('tahun_ajaran_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Tambah Tahun Ajaran',
        'kembali': 'tahun_ajaran_daftar',
    })


@peran_diperlukan('TU')
def tahun_ajaran_ubah(request, pk):
    tahun = get_object_or_404(TahunAjaran, pk=pk)
    form = TahunAjaranForm(request.POST or None, instance=tahun)
    if form.is_valid():
        form.save()
        messages.success(request, f'Tahun ajaran {tahun.nama} diperbarui.')
        return redirect('tahun_ajaran_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Ubah Tahun Ajaran',
        'kembali': 'tahun_ajaran_daftar',
    })


@peran_diperlukan('TU')
def tahun_ajaran_hapus(request, pk):
    tahun = get_object_or_404(TahunAjaran, pk=pk)
    if request.method == 'POST':
        try:
            tahun.delete()
        except ProtectedError:
            messages.error(
                request,
                f'Tahun ajaran {tahun.nama} tidak bisa dihapus karena masih dipakai oleh kelas.',
            )
        else:
            messages.success(request, f'Tahun ajaran {tahun.nama} dihapus.')
        return redirect('tahun_ajaran_daftar')
    return render(request, 'akademik/hapus_umum.html', {
        'judul': 'Hapus tahun ajaran?',
        'nama_objek': tahun.nama,
        'keterangan': '',
        'kembali': 'tahun_ajaran_daftar',
    })


# ===== Mata Pelajaran =====

@peran_diperlukan('TU')
def mapel_daftar(request):
    return render(request, 'akademik/mapel_daftar.html', {
        'daftar': MataPelajaran.objects.all(),
    })


@peran_diperlukan('TU')
def mapel_tambah(request):
    form = MataPelajaranForm(request.POST or None)
    if form.is_valid():
        mapel = form.save()
        messages.success(request, f'Mata pelajaran {mapel.nama} ditambahkan.')
        return redirect('mapel_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Tambah Mata Pelajaran',
        'kembali': 'mapel_daftar',
    })


@peran_diperlukan('TU')
def mapel_ubah(request, pk):
    mapel = get_object_or_404(MataPelajaran, pk=pk)
    form = MataPelajaranForm(request.POST or None, instance=mapel)
    if form.is_valid():
        form.save()
        messages.success(request, f'Mata pelajaran {mapel.nama} diperbarui.')
        return redirect('mapel_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Ubah Mata Pelajaran',
        'kembali': 'mapel_daftar',
    })


@peran_diperlukan('TU')
def mapel_hapus(request, pk):
    mapel = get_object_or_404(MataPelajaran, pk=pk)
    if request.method == 'POST':
        try:
            mapel.delete()
        except ProtectedError:
            messages.error(
                request,
                f'Mata pelajaran {mapel.nama} tidak bisa dihapus karena masih dipakai.',
            )
        else:
            messages.success(request, f'Mata pelajaran {mapel.nama} dihapus.')
        return redirect('mapel_daftar')
    return render(request, 'akademik/hapus_umum.html', {
        'judul': 'Hapus mata pelajaran?',
        'nama_objek': mapel.nama,
        'keterangan': '',
        'kembali': 'mapel_daftar',
    })

# ===== Kelas =====

@peran_diperlukan('TU')
def kelas_daftar(request):
    daftar_tahun = TahunAjaran.objects.all()

    tahun_id = request.GET.get('tahun')
    if tahun_id is None:
        tahun_aktif = daftar_tahun.filter(aktif=True).first()
        tahun_id = str(tahun_aktif.pk) if tahun_aktif else ''

    kelas = Kelas.objects.select_related('tahun_ajaran', 'wali_kelas').annotate(
        jumlah_siswa=Count('siswa'),
    )
    if tahun_id:
        kelas = kelas.filter(tahun_ajaran_id=tahun_id)

    return render(request, 'akademik/kelas_daftar.html', {
        'daftar': kelas,
        'daftar_tahun': daftar_tahun,
        'tahun_id': tahun_id,
    })


@peran_diperlukan('TU')
def kelas_detail(request, pk):
    kelas = get_object_or_404(
        Kelas.objects.select_related('tahun_ajaran', 'wali_kelas'), pk=pk,
    )
    return render(request, 'akademik/kelas_detail.html', {
        'kelas': kelas,
        'daftar_siswa': kelas.siswa_set.all(),
    })


@peran_diperlukan('TU')
def kelas_tambah(request):
    tahun_aktif = TahunAjaran.objects.filter(aktif=True).first()
    form = KelasForm(request.POST or None, initial={'tahun_ajaran': tahun_aktif})
    if form.is_valid():
        kelas = form.save()
        messages.success(request, f'Kelas {kelas.nama} ({kelas.tahun_ajaran}) ditambahkan.')
        return redirect(f"{reverse('kelas_daftar')}?tahun={kelas.tahun_ajaran_id}")
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Tambah Kelas',
        'kembali': 'kelas_daftar',
    })


@peran_diperlukan('TU')
def kelas_ubah(request, pk):
    kelas = get_object_or_404(Kelas, pk=pk)
    form = KelasForm(request.POST or None, instance=kelas)
    if form.is_valid():
        kelas = form.save()
        messages.success(request, f'Kelas {kelas.nama} diperbarui.')
        return redirect(f"{reverse('kelas_daftar')}?tahun={kelas.tahun_ajaran_id}")
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Ubah Kelas',
        'kembali': 'kelas_daftar',
    })


@peran_diperlukan('TU')
def kelas_hapus(request, pk):
    kelas = get_object_or_404(Kelas, pk=pk)
    jumlah = kelas.siswa_set.count()
    if request.method == 'POST':
        try:
            kelas.delete()
        except ProtectedError:
            messages.error(request, f'Kelas {kelas.nama} tidak bisa dihapus karena masih dipakai.')
        else:
            messages.success(request, f'Kelas {kelas.nama} dihapus.')
        return redirect('kelas_daftar')

    keterangan = ''
    if jumlah:
        keterangan = f'— {jumlah} siswa di dalamnya tidak ikut terhapus, hanya menjadi tanpa kelas'
    return render(request, 'akademik/hapus_umum.html', {
        'judul': 'Hapus kelas?',
        'nama_objek': f'{kelas.nama} ({kelas.tahun_ajaran})',
        'keterangan': keterangan,
        'kembali': 'kelas_daftar',
    })

# ===== Jam Pelajaran =====

@peran_diperlukan('TU')
def jam_daftar(request):
    return render(request, 'akademik/jam_daftar.html', {
        'daftar': JamPelajaran.objects.all(),
    })


@peran_diperlukan('TU')
def jam_tambah(request):
    terakhir = JamPelajaran.objects.order_by('-urutan').first()
    urutan_berikut = terakhir.urutan + 1 if terakhir else 1
    form = JamPelajaranForm(request.POST or None, initial={'urutan': urutan_berikut})
    if form.is_valid():
        jam = form.save()
        messages.success(request, f'Jam ke-{jam.urutan} ditambahkan.')
        return redirect('jam_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Tambah Jam Pelajaran',
        'kembali': 'jam_daftar',
    })


@peran_diperlukan('TU')
def jam_ubah(request, pk):
    jam = get_object_or_404(JamPelajaran, pk=pk)
    form = JamPelajaranForm(request.POST or None, instance=jam)
    if form.is_valid():
        form.save()
        messages.success(request, f'Jam ke-{jam.urutan} diperbarui.')
        return redirect('jam_daftar')
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Ubah Jam Pelajaran',
        'kembali': 'jam_daftar',
    })


@peran_diperlukan('TU')
def jam_hapus(request, pk):
    jam = get_object_or_404(JamPelajaran, pk=pk)
    if request.method == 'POST':
        try:
            jam.delete()
        except ProtectedError:
            messages.error(
                request,
                f'Jam ke-{jam.urutan} tidak bisa dihapus karena masih dipakai di jadwal.',
            )
        else:
            messages.success(request, f'Jam ke-{jam.urutan} dihapus.')
        return redirect('jam_daftar')
    return render(request, 'akademik/hapus_umum.html', {
        'judul': 'Hapus jam pelajaran?',
        'nama_objek': str(jam),
        'keterangan': '',
        'kembali': 'jam_daftar',
    })

# ===== Jadwal Pelajaran =====

@peran_diperlukan('TU')
def jadwal_daftar(request):
    daftar_kelas = Kelas.objects.select_related('tahun_ajaran')

    kelas = None
    kelas_id = request.GET.get('kelas', '')
    if kelas_id.isdigit():
        kelas = daftar_kelas.filter(pk=kelas_id).first()
    if kelas is None:
        kelas = daftar_kelas.filter(tahun_ajaran__aktif=True).first() or daftar_kelas.first()

    baris = []
    if kelas:
        baris = _susun_baris(
            Jadwal.objects.filter(kelas=kelas).select_related('mapel', 'guru', 'jam')
        )

    return render(request, 'akademik/jadwal_daftar.html', {
        'kelas': kelas,
        'daftar_kelas': daftar_kelas,
        'daftar_hari': Jadwal.Hari.choices,
        'baris': baris,
    })


@peran_diperlukan('TU')
def jadwal_tambah(request):
    awal = {}
    for nama in ('kelas', 'hari', 'jam'):
        nilai = request.GET.get(nama, '')
        if nilai.isdigit():
            awal[nama] = nilai

    form = JadwalForm(request.POST or None, initial=awal)
    if form.is_valid():
        jadwal = form.save()
        messages.success(request, 'Jadwal ditambahkan.')
        return redirect(f"{reverse('jadwal_daftar')}?kelas={jadwal.kelas_id}")
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Tambah Jadwal',
        'kembali': 'jadwal_daftar',
    })


@peran_diperlukan('TU')
def jadwal_ubah(request, pk):
    jadwal = get_object_or_404(Jadwal, pk=pk)
    form = JadwalForm(request.POST or None, instance=jadwal)
    if form.is_valid():
        jadwal = form.save()
        messages.success(request, 'Jadwal diperbarui.')
        return redirect(f"{reverse('jadwal_daftar')}?kelas={jadwal.kelas_id}")
    return render(request, 'akademik/form_umum.html', {
        'form': form,
        'judul': 'Ubah Jadwal',
        'kembali': 'jadwal_daftar',
        'hapus_url': reverse('jadwal_hapus', args=[jadwal.pk]),
    })


@peran_diperlukan('TU')
def jadwal_hapus(request, pk):
    jadwal = get_object_or_404(Jadwal, pk=pk)
    kelas_id = jadwal.kelas_id
    if request.method == 'POST':
        try:
            jadwal.delete()
        except ProtectedError:
            messages.error(request, 'Jadwal tidak bisa dihapus karena sudah dipakai.')
        else:
            messages.success(request, 'Jadwal dihapus.')
        return redirect(f"{reverse('jadwal_daftar')}?kelas={kelas_id}")
    return render(request, 'akademik/hapus_umum.html', {
        'judul': 'Hapus jadwal?',
        'nama_objek': str(jadwal),
        'keterangan': '',
        'kembali': 'jadwal_daftar',
    })

# ===== Alat bantu: menyusun tabel jadwal mingguan =====

def _susun_baris(jadwal_qs):
    """Mengubah daftar jadwal menjadi baris tabel: satu baris per jam, satu kotak per hari."""
    peta = {(j.hari, j.jam_id): j for j in jadwal_qs}
    baris = []
    for jam in JamPelajaran.objects.all():
        sel = [
            {'hari': nilai, 'jadwal': peta.get((nilai, jam.pk))}
            for nilai, _nama in Jadwal.Hari.choices
        ]
        baris.append({'jam': jam, 'sel': sel})
    return baris

# ===== Jadwal untuk Guru dan Siswa (hanya baca) =====

@peran_diperlukan('GURU')
def jadwal_guru(request):
    guru = Guru.objects.filter(pengguna=request.user).first()
    tahun = TahunAjaran.objects.filter(aktif=True).first()

    catatan = ''
    baris = []
    if guru is None:
        catatan = 'Akun Anda belum terhubung dengan data guru. Hubungi TU.'
    elif tahun is None:
        catatan = 'Belum ada tahun ajaran yang aktif. Hubungi TU.'
    else:
        baris = _susun_baris(
            Jadwal.objects.filter(guru=guru, kelas__tahun_ajaran=tahun)
            .select_related('mapel', 'kelas', 'jam')
        )
        if not baris:
            catatan = 'Belum ada jam pelajaran yang diatur. Hubungi TU.'

    return render(request, 'akademik/jadwal_lihat.html', {
        'judul': 'Jadwal Mengajar',
        'subjudul': f'{guru.nama} · Tahun ajaran {tahun}' if guru and tahun else '',
        'mode': 'guru',
        'catatan': catatan,
        'baris': baris,
        'daftar_hari': Jadwal.Hari.choices,
    })


@peran_diperlukan('SISWA')
def jadwal_siswa(request):
    siswa = (Siswa.objects.filter(pengguna=request.user)
             .select_related('kelas__tahun_ajaran').first())
    kelas = siswa.kelas if siswa else None

    catatan = ''
    baris = []
    if siswa is None:
        catatan = 'Akun Anda belum terhubung dengan data siswa. Hubungi TU.'
    elif kelas is None:
        catatan = 'Anda belum ditempatkan di kelas mana pun. Hubungi TU.'
    else:
        baris = _susun_baris(
            Jadwal.objects.filter(kelas=kelas).select_related('mapel', 'guru', 'jam')
        )
        if not baris:
            catatan = 'Belum ada jam pelajaran yang diatur. Hubungi TU.'

    return render(request, 'akademik/jadwal_lihat.html', {
        'judul': 'Jadwal Pelajaran',
        'subjudul': f'Kelas {kelas.nama} · Tahun ajaran {kelas.tahun_ajaran}' if kelas else '',
        'mode': 'siswa',
        'catatan': catatan,
        'baris': baris,
        'daftar_hari': Jadwal.Hari.choices,
    })

# ===== Absensi Harian =====

def _kelas_absensi(user):
    """Kelas yang boleh diabsen oleh pengguna ini, di tahun ajaran aktif."""
    tahun = TahunAjaran.objects.filter(aktif=True).first()
    if tahun is None:
        return Kelas.objects.none()
    kelas = Kelas.objects.select_related('tahun_ajaran').filter(tahun_ajaran=tahun)
    if user.peran == 'GURU':
        kelas = kelas.filter(wali_kelas__pengguna=user)
    return kelas


def _pilih_kelas(request, daftar_kelas):
    kelas_id = request.GET.get('kelas', '')
    kelas = None
    if kelas_id.isdigit():
        kelas = daftar_kelas.filter(pk=kelas_id).first()
    return kelas or daftar_kelas.first()


def _baca_tanggal(teks, bawaan):
    try:
        return datetime.date.fromisoformat(teks)
    except (TypeError, ValueError):
        return bawaan


def _baca_bulan(teks, bawaan):
    try:
        tahun, bulan = teks.split('-')
        return datetime.date(int(tahun), int(bulan), 1)
    except (AttributeError, ValueError):
        return bawaan


@peran_diperlukan('GURU', 'TU')
def absensi_harian(request):
    hari_ini = timezone.localdate()
    daftar_kelas = _kelas_absensi(request.user)
    kelas = _pilih_kelas(request, daftar_kelas)

    tanggal = _baca_tanggal(request.GET.get('tanggal'), hari_ini)
    if tanggal > hari_ini:
        tanggal = hari_ini
        messages.error(request, 'Tanggal absensi tidak boleh di masa depan. Dikembalikan ke hari ini.')

    catatan = ''
    if kelas is None:
        if request.user.peran == 'GURU':
            catatan = 'Anda belum ditetapkan sebagai wali kelas di tahun ajaran aktif. Hubungi TU.'
        else:
            catatan = 'Belum ada kelas di tahun ajaran aktif.'

    daftar_siswa = Siswa.objects.none()
    if kelas:
        daftar_siswa = Siswa.objects.filter(kelas=kelas).order_by('nama')

    if request.method == 'POST' and kelas:
        hitung = {kode: 0 for kode, _nama in AbsensiHarian.Status.choices}
        with transaction.atomic():
            for siswa in daftar_siswa:
                status = request.POST.get(f'status_{siswa.pk}')
                if status not in hitung:
                    continue
                AbsensiHarian.objects.update_or_create(
                    siswa=siswa,
                    tanggal=tanggal,
                    defaults={
                        'kelas': kelas,
                        'status': status,
                        'keterangan': request.POST.get(f'ket_{siswa.pk}', '').strip()[:200],
                        'dicatat_oleh': request.user,
                    },
                )
                hitung[status] += 1
        ringkas = ', '.join(
            f'{hitung[kode]} {nama.lower()}' for kode, nama in AbsensiHarian.Status.choices
        )
        messages.success(
            request,
            f'Absensi kelas {kelas.nama} tanggal {tanggal:%d/%m/%Y} disimpan: {ringkas}.',
        )
        return redirect(
            f"{reverse('absensi_harian')}?kelas={kelas.pk}&tanggal={tanggal.isoformat()}"
        )

    tersimpan = {
        a.siswa_id: a
        for a in AbsensiHarian.objects.filter(siswa__in=daftar_siswa, tanggal=tanggal)
    }
    baris = []
    for siswa in daftar_siswa:
        a = tersimpan.get(siswa.pk)
        baris.append({
            'siswa': siswa,
            'status': a.status if a else AbsensiHarian.Status.HADIR,
            'keterangan': a.keterangan if a else '',
        })

    return render(request, 'akademik/absensi_harian.html', {
        'kelas': kelas,
        'daftar_kelas': daftar_kelas,
        'tanggal': tanggal,
        'hari_ini': hari_ini,
        'baris': baris,
        'sudah_tercatat': bool(tersimpan),
        'daftar_status': AbsensiHarian.Status.choices,
        'catatan': catatan,
    })


@peran_diperlukan('GURU', 'TU')
def absensi_rekap(request):
    hari_ini = timezone.localdate()
    daftar_kelas = _kelas_absensi(request.user)
    kelas = _pilih_kelas(request, daftar_kelas)
    bulan = _baca_bulan(request.GET.get('bulan'), hari_ini.replace(day=1))

    catatan = ''
    baris = []
    if kelas is None:
        catatan = 'Belum ada kelas yang bisa direkap. Anda harus menjadi wali kelas, atau hubungi TU.'
    else:
        dalam_bulan = Q(
            absensiharian__tanggal__year=bulan.year,
            absensiharian__tanggal__month=bulan.month,
        )
        siswa_qs = Siswa.objects.filter(kelas=kelas).annotate(
            hadir=Count('absensiharian', filter=dalam_bulan & Q(absensiharian__status='HADIR')),
            sakit=Count('absensiharian', filter=dalam_bulan & Q(absensiharian__status='SAKIT')),
            izin=Count('absensiharian', filter=dalam_bulan & Q(absensiharian__status='IZIN')),
            alpa=Count('absensiharian', filter=dalam_bulan & Q(absensiharian__status='ALPA')),
        ).order_by('nama')
        for siswa in siswa_qs:
            total = siswa.hadir + siswa.sakit + siswa.izin + siswa.alpa
            persen = round(siswa.hadir * 100 / total) if total else None
            baris.append({'siswa': siswa, 'total': total, 'persen': persen})

    return render(request, 'akademik/absensi_rekap.html', {
        'kelas': kelas,
        'daftar_kelas': daftar_kelas,
        'bulan': bulan,
        'hari_ini': hari_ini,
        'baris': baris,
        'catatan': catatan,
    })

# ===== Absensi per Pelajaran =====

@peran_diperlukan('GURU', 'TU')
def absensi_pelajaran(request):
    hari_ini = timezone.localdate()
    tanggal = _baca_tanggal(request.GET.get('tanggal'), hari_ini)
    if tanggal > hari_ini:
        tanggal = hari_ini
        messages.error(request, 'Tanggal absensi tidak boleh di masa depan. Dikembalikan ke hari ini.')

    tahun = TahunAjaran.objects.filter(aktif=True).first()
    guru = None
    catatan = ''
    if request.user.peran == 'GURU':
        guru = Guru.objects.filter(pengguna=request.user).first()
        if guru is None:
            catatan = 'Akun Anda belum terhubung dengan data guru. Hubungi TU.'
    if not catatan and tahun is None:
        catatan = 'Belum ada tahun ajaran yang aktif.'

    nomor_hari = tanggal.isoweekday()
    nama_hari = Jadwal.Hari(nomor_hari).label if nomor_hari in Jadwal.Hari.values else 'Minggu'

    daftar = []
    if not catatan:
        dasar = Jadwal.objects.filter(kelas__tahun_ajaran=tahun, hari=nomor_hari)
        if guru:
            dasar = dasar.filter(guru=guru)
        daftar = (
            dasar.select_related('kelas', 'mapel', 'guru', 'jam')
            .annotate(
                tercatat=Count(
                    'absensipelajaran',
                    filter=Q(absensipelajaran__tanggal=tanggal),
                ),
                tidak_hadir=Count(
                    'absensipelajaran',
                    filter=Q(
                        absensipelajaran__tanggal=tanggal,
                        absensipelajaran__status__in=['SAKIT', 'IZIN', 'ALPA'],
                    ),
                ),
            )
            .order_by('jam__urutan', 'kelas__nama')
        )

    return render(request, 'akademik/absensi_pelajaran.html', {
        'daftar': daftar,
        'tanggal': tanggal,
        'hari_ini': hari_ini,
        'nama_hari': nama_hari,
        'catatan': catatan,
    })


@peran_diperlukan('GURU', 'TU')
def absensi_pelajaran_isi(request, pk):
    jadwal = get_object_or_404(
        Jadwal.objects.select_related('kelas__tahun_ajaran', 'mapel', 'guru', 'jam'),
        pk=pk,
    )
    if request.user.peran == 'GURU' and jadwal.guru.pengguna_id != request.user.pk:
        raise PermissionDenied

    hari_ini = timezone.localdate()
    tanggal = _baca_tanggal(request.GET.get('tanggal'), hari_ini)
    kembali = f"{reverse('absensi_pelajaran')}?tanggal={tanggal.isoformat()}"

    if not jadwal.kelas.tahun_ajaran.aktif:
        messages.error(request, 'Absensi hanya bisa diisi untuk tahun ajaran yang aktif.')
        return redirect(kembali)
    if tanggal > hari_ini or tanggal.isoweekday() != jadwal.hari:
        messages.error(
            request,
            'Tanggal tidak sesuai dengan hari jadwal pelajaran ini, atau berada di masa depan.',
        )
        return redirect(kembali)

    daftar_siswa = Siswa.objects.filter(kelas=jadwal.kelas).order_by('nama')

    if request.method == 'POST':
        hitung = {kode: 0 for kode, _nama in AbsensiHarian.Status.choices}
        with transaction.atomic():
            for siswa in daftar_siswa:
                status = request.POST.get(f'status_{siswa.pk}')
                if status not in hitung:
                    continue
                AbsensiPelajaran.objects.update_or_create(
                    jadwal=jadwal,
                    siswa=siswa,
                    tanggal=tanggal,
                    defaults={
                        'status': status,
                        'keterangan': request.POST.get(f'ket_{siswa.pk}', '').strip()[:200],
                        'dicatat_oleh': request.user,
                    },
                )
                hitung[status] += 1
        ringkas = ', '.join(
            f'{hitung[kode]} {nama.lower()}' for kode, nama in AbsensiHarian.Status.choices
        )
        messages.success(
            request,
            f'Absensi {jadwal.mapel.nama} kelas {jadwal.kelas.nama} '
            f'tanggal {tanggal:%d/%m/%Y} disimpan: {ringkas}.',
        )
        return redirect(kembali)

    tersimpan = {
        a.siswa_id: a
        for a in AbsensiPelajaran.objects.filter(jadwal=jadwal, tanggal=tanggal)
    }
    baris = []
    for siswa in daftar_siswa:
        a = tersimpan.get(siswa.pk)
        baris.append({
            'siswa': siswa,
            'status': a.status if a else AbsensiHarian.Status.HADIR,
            'keterangan': a.keterangan if a else '',
        })

    return render(request, 'akademik/absensi_pelajaran_isi.html', {
        'jadwal': jadwal,
        'tanggal': tanggal,
        'baris': baris,
        'daftar_status': AbsensiHarian.Status.choices,
        'kembali': kembali,
    })

# ===== Nilai =====

def _baca_angka(teks):
    """Mengubah isian teks menjadi angka 0-100. Mengembalikan (angka, pesan_galat)."""
    teks = (teks or '').strip().replace(',', '.')
    if teks == '':
        return None, ''
    try:
        angka = Decimal(teks)
    except InvalidOperation:
        return None, 'bukan angka'
    if not angka.is_finite():
        return None, 'bukan angka'
    if angka < 0 or angka > 100:
        return None, 'harus antara 0 dan 100'
    return angka.quantize(Decimal('0.01')), ''


def _teks_angka(angka):
    """Menampilkan angka tanpa nol di belakang koma: 85.00 menjadi '85', 82.50 menjadi '82.5'."""
    if angka is None:
        return ''
    teks = f'{angka:f}'
    return teks.rstrip('0').rstrip('.') if '.' in teks else teks


@peran_diperlukan('GURU', 'TU')
def nilai_daftar(request):
    tahun = TahunAjaran.objects.filter(aktif=True).first()
    guru = None
    catatan = ''
    if request.user.peran == 'GURU':
        guru = Guru.objects.filter(pengguna=request.user).first()
        if guru is None:
            catatan = 'Akun Anda belum terhubung dengan data guru. Hubungi TU.'
    if not catatan and tahun is None:
        catatan = 'Belum ada tahun ajaran yang aktif.'

    daftar = []
    if not catatan:
        dasar = Jadwal.objects.filter(kelas__tahun_ajaran=tahun)
        if guru:
            dasar = dasar.filter(guru=guru)
        daftar = (
            dasar.values('kelas_id', 'kelas__nama', 'mapel_id', 'mapel__nama', 'guru__nama')
            .distinct()
            .order_by('kelas__nama', 'mapel__nama')
        )

    return render(request, 'akademik/nilai_daftar.html', {
        'daftar': daftar,
        'tahun': tahun,
        'catatan': catatan,
    })


@peran_diperlukan('GURU', 'TU')
def nilai_isi(request, kelas_id, mapel_id):
    kelas = get_object_or_404(Kelas.objects.select_related('tahun_ajaran'), pk=kelas_id)
    mapel = get_object_or_404(MataPelajaran, pk=mapel_id)

    mengajar = Jadwal.objects.filter(kelas=kelas, mapel=mapel)
    if request.user.peran == 'GURU':
        mengajar = mengajar.filter(guru__pengguna=request.user)
    if not mengajar.exists():
        raise PermissionDenied

    if not kelas.tahun_ajaran.aktif:
        messages.error(request, 'Nilai hanya bisa diisi untuk tahun ajaran yang aktif.')
        return redirect('nilai_daftar')

    semester = request.GET.get('semester')
    if semester not in Semester.values:
        semester = kelas.tahun_ajaran.semester_aktif

    daftar_siswa = Siswa.objects.filter(kelas=kelas).order_by('nama')
    tersimpan = {
        n.siswa_id: n
        for n in Nilai.objects.filter(kelas=kelas, mapel=mapel, semester=semester)
        .select_related('mapel')
    }

    baris = []
    if request.method == 'POST':
        hasil = []
        galat = []
        for siswa in daftar_siswa:
            isian = {}
            for komponen in ('tugas', 'uts', 'uas'):
                teks = request.POST.get(f'{komponen}_{siswa.pk}', '')
                angka, pesan = _baca_angka(teks)
                if pesan:
                    galat.append(f'{siswa.nama} ({komponen.upper()}) {pesan}')
                isian[komponen] = (teks, angka)
            hasil.append((siswa, isian))

        if not galat:
            with transaction.atomic():
                for siswa, isian in hasil:
                    nilai = tersimpan.get(siswa.pk)
                    semua_kosong = all(angka is None for _teks, angka in isian.values())
                    if nilai is None:
                        if semua_kosong:
                            continue
                        nilai = Nilai(siswa=siswa, mapel=mapel, kelas=kelas, semester=semester)
                    nilai.tugas = isian['tugas'][1]
                    nilai.uts = isian['uts'][1]
                    nilai.uas = isian['uas'][1]
                    nilai.dicatat_oleh = request.user
                    nilai.save()
            messages.success(
                request,
                f'Nilai {mapel.nama} kelas {kelas.nama} semester '
                f'{Semester(semester).label} disimpan.',
            )
            return redirect(f'{request.path}?semester={semester}')

        ringkas = '; '.join(galat[:4]) + (' dan lainnya' if len(galat) > 4 else '')
        messages.error(request, f'Nilai belum disimpan. Periksa isian: {ringkas}.')
        baris = [
            {
                'siswa': siswa,
                'tugas': isian['tugas'][0],
                'uts': isian['uts'][0],
                'uas': isian['uas'][0],
                'nilai': None,
            }
            for siswa, isian in hasil
        ]
    else:
        for siswa in daftar_siswa:
            nilai = tersimpan.get(siswa.pk)
            baris.append({
                'siswa': siswa,
                'tugas': _teks_angka(nilai.tugas) if nilai else '',
                'uts': _teks_angka(nilai.uts) if nilai else '',
                'uas': _teks_angka(nilai.uas) if nilai else '',
                'nilai': nilai,
            })

    return render(request, 'akademik/nilai_isi.html', {
        'kelas': kelas,
        'mapel': mapel,
        'semester': semester,
        'daftar_semester': Semester.choices,
        'baris': baris,
        'bobot': settings.BOBOT_NILAI,
    })


@peran_diperlukan('SISWA')
def nilai_siswa(request):
    siswa = (Siswa.objects.filter(pengguna=request.user)
             .select_related('kelas__tahun_ajaran').first())
    kelas = siswa.kelas if siswa else None

    catatan = ''
    baris = []
    semester = ''
    rata_rata = None
    if siswa is None:
        catatan = 'Akun Anda belum terhubung dengan data siswa. Hubungi TU.'
    elif kelas is None:
        catatan = 'Anda belum ditempatkan di kelas mana pun. Hubungi TU.'
    else:
        semester = request.GET.get('semester')
        if semester not in Semester.values:
            semester = kelas.tahun_ajaran.semester_aktif
        baris, rata_rata = _baris_nilai(siswa, kelas, semester)

    return render(request, 'akademik/nilai_siswa.html', {
        'siswa': siswa,
        'kelas': kelas,
        'semester': semester,
        'daftar_semester': Semester.choices,
        'baris': baris,
        'rata_rata': rata_rata,
        'catatan': catatan,
    })

# ===== Alat bantu untuk Leger dan Rapor =====

def _baris_nilai(siswa, kelas, semester):
    """Daftar mapel beserta nilai siswa pada satu semester, dan rata-rata nilai akhirnya."""
    nilai_peta = {
        n.mapel_id: n
        for n in Nilai.objects.filter(siswa=siswa, kelas=kelas, semester=semester)
        .select_related('mapel')
    }
    id_mapel = set(
        Jadwal.objects.filter(kelas=kelas).values_list('mapel_id', flat=True)
    ) | set(nilai_peta)
    baris = [
        {'mapel': mapel, 'nilai': nilai_peta.get(mapel.pk)}
        for mapel in MataPelajaran.objects.filter(pk__in=id_mapel)
    ]
    akhir = [
        b['nilai'].nilai_akhir for b in baris
        if b['nilai'] and b['nilai'].nilai_akhir is not None
    ]
    rata_rata = round(sum(akhir) / len(akhir), 2) if akhir else None
    return baris, rata_rata


def _hitung_rata_dan_peringkat(kelas, semester):
    """Rata-rata nilai akhir tiap siswa di satu kelas, beserta peringkatnya."""
    data = (
        Nilai.objects.filter(kelas=kelas, semester=semester, nilai_akhir__isnull=False)
        .values('siswa_id')
        .annotate(rata=Avg('nilai_akhir'))
        .order_by('-rata')
    )
    hasil = {}
    peringkat = 0
    sebelumnya = None
    for urutan, d in enumerate(data, start=1):
        rata = round(d['rata'], 2)
        if rata != sebelumnya:
            peringkat = urutan
            sebelumnya = rata
        hasil[d['siswa_id']] = {'rata': rata, 'peringkat': peringkat}
    return hasil


def _periode_semester(tahun, semester):
    """Rentang tanggal bawaan sebuah semester, dari nama tahun ajaran seperti 2025/2026."""
    try:
        awal = int(tahun.nama.split('/')[0])
    except (ValueError, IndexError):
        awal = timezone.localdate().year
    if semester == Semester.GANJIL:
        return datetime.date(awal, 7, 1), datetime.date(awal, 12, 31)
    return datetime.date(awal + 1, 1, 1), datetime.date(awal + 1, 6, 30)


def _boleh_lihat_rapor(user, siswa):
    if user.peran == 'TU':
        return True
    if user.peran == 'GURU':
        kelas = siswa.kelas
        return bool(
            kelas and kelas.wali_kelas and kelas.wali_kelas.pengguna_id == user.pk
        )
    if user.peran == 'SISWA':
        return siswa.pengguna_id == user.pk
    return False

    # ===== Leger dan Rapor =====

@peran_diperlukan('GURU', 'TU')
def leger(request):
    daftar_kelas = _kelas_absensi(request.user)
    kelas = _pilih_kelas(request, daftar_kelas)

    catatan = ''
    semester = ''
    daftar_mapel = []
    baris = []
    if kelas is None:
        if request.user.peran == 'GURU':
            catatan = 'Anda belum ditetapkan sebagai wali kelas di tahun ajaran aktif. Hubungi TU.'
        else:
            catatan = 'Belum ada kelas di tahun ajaran aktif.'
    else:
        semester = request.GET.get('semester')
        if semester not in Semester.values:
            semester = kelas.tahun_ajaran.semester_aktif

        peta = {
            (n.siswa_id, n.mapel_id): n.nilai_akhir
            for n in Nilai.objects.filter(kelas=kelas, semester=semester)
        }
        id_mapel = set(
            Jadwal.objects.filter(kelas=kelas).values_list('mapel_id', flat=True)
        ) | {id_m for (_id_s, id_m) in peta}
        daftar_mapel = list(MataPelajaran.objects.filter(pk__in=id_mapel))

        peringkat = _hitung_rata_dan_peringkat(kelas, semester)
        for siswa in Siswa.objects.filter(kelas=kelas).order_by('nama'):
            sel = []
            for mapel in daftar_mapel:
                nilai = peta.get((siswa.pk, mapel.pk))
                sel.append({'nilai': nilai, 'kurang': nilai is not None and nilai < mapel.kkm})
            info = peringkat.get(siswa.pk)
            baris.append({
                'siswa': siswa,
                'sel': sel,
                'rata': info['rata'] if info else None,
                'peringkat': info['peringkat'] if info else None,
            })

    return render(request, 'akademik/leger.html', {
        'kelas': kelas,
        'daftar_kelas': daftar_kelas,
        'semester': semester,
        'daftar_semester': Semester.choices,
        'daftar_mapel': daftar_mapel,
        'baris': baris,
        'catatan': catatan,
    })


@peran_diperlukan('GURU', 'TU', 'SISWA')
def rapor(request, siswa_id):
    siswa = get_object_or_404(
        Siswa.objects.select_related('kelas__tahun_ajaran', 'kelas__wali_kelas'),
        pk=siswa_id,
    )
    if not _boleh_lihat_rapor(request.user, siswa):
        raise PermissionDenied

    kelas = siswa.kelas
    if kelas is None:
        return render(request, 'akademik/rapor.html', {
            'siswa': siswa,
            'catatan': 'Siswa ini belum ditempatkan di kelas mana pun.',
        })

    tahun = kelas.tahun_ajaran
    semester = request.GET.get('semester')
    if semester not in Semester.values:
        semester = tahun.semester_aktif

    awal_bawaan, akhir_bawaan = _periode_semester(tahun, semester)
    dari = _baca_tanggal(request.GET.get('dari'), awal_bawaan)
    sampai = _baca_tanggal(request.GET.get('sampai'), akhir_bawaan)
    if sampai < dari:
        dari, sampai = awal_bawaan, akhir_bawaan

    baris, rata_rata = _baris_nilai(siswa, kelas, semester)
    info = _hitung_rata_dan_peringkat(kelas, semester).get(siswa.pk)

    hitung = {kode: 0 for kode, _nama in AbsensiHarian.Status.choices}
    rekap = (
        AbsensiHarian.objects.filter(siswa=siswa, tanggal__range=(dari, sampai))
        .values('status').annotate(jumlah=Count('id'))
    )
    for r in rekap:
        hitung[r['status']] = r['jumlah']

    return render(request, 'akademik/rapor.html', {
        'siswa': siswa,
        'kelas': kelas,
        'tahun': tahun,
        'semester': semester,
        'semester_label': Semester(semester).label,
        'daftar_semester': Semester.choices,
        'baris': baris,
        'rata_rata': rata_rata,
        'peringkat': info['peringkat'] if info else None,
        'jumlah_siswa': Siswa.objects.filter(kelas=kelas).count(),
        'dari': dari,
        'sampai': sampai,
        'hadir': hitung['HADIR'],
        'sakit': hitung['SAKIT'],
        'izin': hitung['IZIN'],
        'alpa': hitung['ALPA'],
        'total_hari': sum(hitung.values()),
        'wali_kelas': kelas.wali_kelas,
        'nama_sekolah': settings.NAMA_SEKOLAH,
        'alamat_sekolah': settings.ALAMAT_SEKOLAH,
        'kepala_sekolah': settings.NAMA_KEPALA_SEKOLAH,
        'hari_ini': timezone.localdate(),
        'catatan': '',
    })