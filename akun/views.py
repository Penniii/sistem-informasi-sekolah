from akademik.statistik import ringkasan_tu

from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .decorators import peran_diperlukan


@login_required
def dashboard(request):
    konteks = {}
    if request.user.peran == 'TU':
        konteks['stat'] = ringkasan_tu()
    return render(request, 'akun/dashboard.html', konteks)

@peran_diperlukan('TU')
def halaman_uji_tu(request):
    return HttpResponse('Halaman ini hanya bisa dibuka oleh Tata Usaha.')

class GantiPasswordView(PasswordChangeView):
    template_name = 'akun/ganti_password.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.wajib_ganti_password = False
        self.request.user.save(update_fields=['wajib_ganti_password'])
        messages.success(self.request, 'Password berhasil diganti.')
        return response