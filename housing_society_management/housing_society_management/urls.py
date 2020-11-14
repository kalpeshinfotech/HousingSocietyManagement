"""housing_society_management URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from ajax_select import urls as ajax_select_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from hsm import helpdesk, maintenance, models, society

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('hsm/get_wings_by_society/', society.get_wings_by_society, name='get_wings_by_society'),
                  path('ajax_select/', include(ajax_select_urls)),
                  path('ajax_select/', include(ajax_select_urls)),
                  path('ajax_select/', include(ajax_select_urls)),
                  path('maintenance_datatable', (maintenance.MaintenanceDataTable.as_view()),
                       name='maintenance_datatable'),
                  # path('home/', include('hsm.urls')),
                  # path('register/', include('hsm.urls')),
                  # path('login/', auth_views.LoginView.as_view(template_name='hsm/login.html'), name='login'),
                  # path('logout/', auth_views.LogoutView.as_view(template_name='hsm/logout.html'), name='logout'),
                  # path('password-reset/done',
                  #      auth_views.PasswordResetDoneView.as_view(template_name='hsm/password_reset_done.html'),
                  #      name='password_reset_done'),
                  # path('password-reset/',
                  #      auth_views.PasswordResetView.as_view(template_name='hsm/password_reset.html'),
                  #      name='password_reset'),
                  # path('password-reset-confirm/<uidb64>/<token>/',
                  #      auth_views.PasswordResetConfirmView.as_view(template_name='hsm/password_reset_confirm.html'),
                  #      name='password_reset_confirm'),
                  # path('profile/', include('hsm.urls')),
                  # path('notice/', include('hsm.urls')),
                  # path('helpdesk/', include('hsm.urls')),
                  # path('mycomplaints/', include('hsm.urls')),
                  # path('mymaintenance/', include('hsm.urls')),
                  path('Society/', include('hsm.urls')),
                  path('ckeditor/', include('ckeditor_uploader.urls')),
                  path('my_complaint_data_tables/', login_required(helpdesk.MyComplaintDatatables.as_view()),
                       name='my_complaint_data_tables'),
                  path('my_Maintenance_data_tables/', login_required(maintenance.MyMaintenanceDatatables.as_view()),
                       name='my_Maintenance_data_tables'),
                  path('Member_data_tables/', login_required(models.MembersDatatables.as_view()),
                       name='Member_data_tables'),
                  # path('rest-auth/', include('rest_auth.urls')),
                  # re_path('api/(?P<version>(v1|v2))/', include('project_apis.urls')),
                  path('mobile_api/', include('mobile_app.urls')),
                  path('', include('dashboard.urls')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
