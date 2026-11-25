from django.shortcuts import redirect
from django.urls import reverse


class WajibGantiPasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and user.wajib_ganti_password:
            halaman_boleh = (reverse('ganti_password'), reverse('logout'))
            if request.path not in halaman_boleh:
                return redirect('ganti_password')
        return self.get_response(request)