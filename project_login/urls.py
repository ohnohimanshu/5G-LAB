from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts import views   # import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # intro at root
    path('', TemplateView.as_view(template_name='intro.html'), name='intro'),

    # expose login, logout, signup at root
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # everything else under accounts/
    path('accounts/', include('accounts.urls')),
]
