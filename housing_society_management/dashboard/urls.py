from django.urls import path

from . import views
from . import datatables
from django.conf import settings
from django.conf.urls.static import static

app_name = 'dashboard'
urlpatterns = [
    # path('', views.dashboard, name="dashboard"),
    # path('login/', views.dashboard_login, name="login"),
    # path('logout/', views.dashboard_logout, name="logout"),
    # path('', views.Dashboard.as_view(), name="dashboard"),
    path('login/', views.Dashboard.as_view(), {'login': ''}, name="login"),
    path('', views.Dashboard.as_view(), name="dashboard"),
    path('logout/', views.Dashboard.as_view(), {'logout': ''}, name="logout"),
    path('maintenance/', views.Maintenance.as_view(), name="maintenance_table"),
    path('filterMaintenanceDate/', views.Maintenance.as_view(), {'filterDate': ''}, name="filter_maintenance_date"),
    path('viewMaintenance/<int:object_id>', views.Maintenance.as_view(), name="view_maintenance"),
    # path('notice/', views.Notice.as_view(), name="notice_table"),
    path('my_notices/', views.Notice.as_view(), name="my_notices"),
    path('filterNoticeDate/', views.Notice.as_view(), {'filterDate': ''},
         name="filter_notice_date"),
    path('viewNotice/<int:object_id>', views.Notice.as_view(), name="view_notice"),
    path('members/', views.Members.as_view(), name="members_table"),
    path('viewMember/<int:object_id>', views.Members.as_view(), name="view_member_detail"),
    path('filterMemberDate/', views.Members.as_view(), {'filterDate': ''},
         name="filter_member_date"),
    path('flats/', views.Flats.as_view(), name="flat_table"),
    path('viewMember/<int:object_id>', views.Flats.as_view(), name="view_member_detail"),
    path('filterFlatDate/', views.Flats.as_view(), {'filterDate': ''},
         name="filter_flat_date"),
    path('helpDesk/', views.HelpDesk.as_view(), name="complaint_table"),
    path('viewCompliant/<int:object_id>', views.HelpDesk.as_view(), name="view_compliant"),
    path('replyCompliant/<int:object_id>', views.HelpDesk.as_view(), {'reply_form': ''}, name="reply_compliant"),
    path('filterComplaintDate/', views.HelpDesk.as_view(), {'filterDate': ''}, name="filter_complaint_date"),
    path('complaint/', views.HelpDesk.as_view(), {'complaint_form': ''}, name="complaint_form"),
    path('account/', views.Accounting.as_view(), name="accounting"),
    path('maintenanceWizard/', datatables.MaintenanceDT.as_view(), name="maintenance_wizard"),
    path('maintenanceServiceWizard/', datatables.MaintenanceServiceDT.as_view(), name="maintenance_service_wizard"),
    path('transaction/', views.Transactions.as_view(), name="transaction_table"),
    path('registerTransaction/', views.Transactions.as_view(), {'register_payment': ''}, name="register_payment"),
    path('accountLine/', datatables.AccountLineDT.as_view(), name="AccountLineDT"),

    path('addNotice/', views.Notice.as_view(), {'add_notice': ''}, name="add_notice"),
    path('profile/', views.Profile.as_view(), name="user_profile"),
    path('flats/', views.Flats.as_view(), name="flats_table"),
    path('vehicle/', views.Vehicle.as_view(), name="vehicle_table"),
    path('purchase_order/', views.PurchaseOrder.as_view(), name="purchase_order_table"),
    path('filterPurchaseOrderDate/', views.PurchaseOrder.as_view(), {'filterDate': ''},
         name="filter_purchase_order_date"),
    path('viewPurchaseOrder/<int:object_id>', views.PurchaseOrder.as_view(), name="view_purchase_order"),
    path('purchase_order_maker/', views.PurchaseOrder.as_view(),
         {'purchase_order_maker': '', 'purchase_order_lines': ''},
         name="purchase_order_maker"),

]
