"""Perhitungan statistik untuk dashboard. Angka dihitung langsung oleh database."""
import datetime

from django.db.models import Avg, Count, F, Max, Q
from django.utils import timezone

from .models import (
    AbsensiHarian, Guru, Kelas, MataPelajaran, Nilai, Siswa, TahunAjaran,
)

WARNA_STATUS = {
    'HADIR': '#16a34a',
    'SAKIT': '#f59e0b',
    'IZIN': '#3b82f6',
    'ALPA': '#dc2626',
}
NAMA_STATUS = {'HADIR': 'Hadir', 'SAKIT': 'Sakit', 'IZIN': 'Izin', 'ALPA': 'Alpa'}


def _persen(bagian, total):
    return round(bagian * 100 / total) if total else 0


def _batang(label, nilai, maksimum, teks):
    """Satu baris grafik batang: lebar batang dalam persen dari nilai maksimum."""
    lebar = max(0, min(100, round(nilai * 100 / maksimum))) if maksimum else 0
    return {'label': label, 'persen': lebar, 'teks': teks}


def _donat(hitung):
    """Teks CSS conic-gradient untuk grafik donat."""
    total = sum(hitung.values())
    if not total:
        return 'conic-gradient(#e2e8f0 0 100%)'
    potongan = []
    awal = 0.0
    for kode, warna in WARNA_STATUS.items():
        akhir = awal + hitung[kode] * 100 / total
        potongan.append(f'{warna} {awal:.2f}% {akhir:.2f}%')
        awal = akhir
    return 'conic-gradient(' + ', '.join(potongan) + ')'


def ringkasan_tu():
    hari_ini = timezone.localdate()
    tahun = TahunAjaran.objects.filter(aktif=True).first()

    hasil = {
        'tahun': tahun,
        'jumlah_siswa': Siswa.objects.count(),
        'jumlah_guru': Guru.objects.count(),
        'jumlah_kelas': Kelas.objects.filter(tahun_ajaran=tahun).count() if tahun else 0,
        'jumlah_mapel': MataPelajaran.objects.count(),
    }

    # 1. Kehadiran pada hari terakhir yang punya data
    tanggal_data = AbsensiHarian.objects.filter(
        tanggal__lte=hari_ini
    ).aggregate(terbaru=Max('tanggal'))['terbaru']

    hitung = {kode: 0 for kode in WARNA_STATUS}
    if tanggal_data:
        rekap = (
            AbsensiHarian.objects.filter(tanggal=tanggal_data)
            .values('status').annotate(jumlah=Count('id'))
        )
        for r in rekap:
            hitung[r['status']] = r['jumlah']
    total = sum(hitung.values())
    hasil['hari_ini'] = {
        'tanggal': tanggal_data,
        'total': total,
        'persen_hadir': _persen(hitung['HADIR'], total),
        'donat': _donat(hitung),
        'legenda': [
            {'nama': NAMA_STATUS[kode], 'jumlah': hitung[kode], 'warna': WARNA_STATUS[kode]}
            for kode in WARNA_STATUS
        ],
    }

    # 2. Tren kehadiran: 7 hari terakhir yang punya data
    tren = list(
        AbsensiHarian.objects.filter(tanggal__lte=hari_ini)
        .values('tanggal')
        .annotate(total=Count('id'), hadir=Count('id', filter=Q(status='HADIR')))
        .order_by('-tanggal')[:7]
    )
    tren.reverse()
    hasil['tren'] = [
        _batang(
            t['tanggal'].strftime('%d/%m'),
            _persen(t['hadir'], t['total']), 100,
            f"{_persen(t['hadir'], t['total'])}%",
        )
        for t in tren
    ]

    # 3 dan 4. Nilai semester yang sedang berjalan
    hasil['nilai_per_kelas'] = []
    hasil['tuntas_per_mapel'] = []
    if tahun:
        nilai_semester = Nilai.objects.filter(
            kelas__tahun_ajaran=tahun,
            semester=tahun.semester_aktif,
            nilai_akhir__isnull=False,
        )

        per_kelas = (
            nilai_semester.values('kelas__nama')
            .annotate(rata=Avg('nilai_akhir'))
            .order_by('kelas__nama')
        )
        hasil['nilai_per_kelas'] = [
            _batang(
                f"Kelas {d['kelas__nama']}", d['rata'], 100,
                f"{d['rata']:.1f}".replace('.', ','),
            )
            for d in per_kelas
        ]

        per_mapel = (
            nilai_semester.values('mapel__nama')
            .annotate(
                total=Count('id'),
                tuntas=Count('id', filter=Q(nilai_akhir__gte=F('mapel__kkm'))),
            )
            .order_by('mapel__nama')
        )
        hasil['tuntas_per_mapel'] = [
            _batang(
                d['mapel__nama'],
                _persen(d['tuntas'], d['total']), 100,
                f"{_persen(d['tuntas'], d['total'])}%",
            )
            for d in per_mapel
        ]

    # 5. Siswa yang perlu perhatian: alpa terbanyak 30 hari terakhir
    batas = hari_ini - datetime.timedelta(days=30)
    perhatian = (
        AbsensiHarian.objects.filter(status='ALPA', tanggal__gte=batas, tanggal__lte=hari_ini)
        .values('siswa__nama', 'siswa__kelas__nama')
        .annotate(jumlah=Count('id'))
        .order_by('-jumlah', 'siswa__nama')[:5]
    )
    hasil['perhatian'] = [
        {'nama': d['siswa__nama'], 'kelas': d['siswa__kelas__nama'], 'jumlah': d['jumlah']}
        for d in perhatian
    ]

    return hasil