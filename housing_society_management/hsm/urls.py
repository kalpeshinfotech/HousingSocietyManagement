from django.urls import path

from . import views
from .reports import PurchaseOrderReport
urlpatterns = [
    # path(r'^pdf/', PurchaseOrderReport.as_view())

    # path('', views.hsm_Home, name='hsm_Home'),
    # path('register/', views.hsm_register, name='hsm_register'),
    # path('profile/', views.hsm_profile, name='hsm_profile'),
    # path('notice/', views.hsm_notice, name='hsm_notice'),
    # path('helpdesk/', views.hsm_helpdesk, name='hsm_helpdesk'),
    # path('mycomplaints/', views.hsm_my_complaints, name='hsm_my_complaints'),
    # path('mymaintenance/', views.hsm_my_maintenance, name='hsm_my_maintenance'),
    # path('Society/', views.hsm_Society_Mem_Details, name='hsm_Society_Mem_Details'),
]
