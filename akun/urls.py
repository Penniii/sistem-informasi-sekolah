from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='akun/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('uji-tu/', views.halaman_uji_tu, name='uji_tu'),
        path('ganti-password/', views.GantiPasswordView.as_view(), name='ganti_password'),
]