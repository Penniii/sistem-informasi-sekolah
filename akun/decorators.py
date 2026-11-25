from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def peran_diperlukan(*daftar_peran):
    def dekorator(fungsi_view):
        @wraps(fungsi_view)
        def pembungkus(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.peran not in daftar_peran:
                raise PermissionDenied
            return fungsi_view(request, *args, **kwargs)
        return pembungkus
    return dekorator