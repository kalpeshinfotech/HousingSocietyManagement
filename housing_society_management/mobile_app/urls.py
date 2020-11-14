from django.urls import path
from .views import MaintenanceAPI, MembersAPI, HelpDeskAPI, AccountingAPI, FlatsAPI, UserAPI, VehicleAPI, NoticeAPI,\
    ComplaintTypeAPI, MaintenanceReportAPI, PurchaseOrderAPI, PurchaseOrderReportAPI, AppToken, HelpDeskReportAPI,\
    NoticeReportAPI

urlpatterns = [
    path('api-token-auth/', AppToken.as_view()),
    path('MaintenanceAPI/', MaintenanceAPI.as_view()),
    path('MembersAPI/', MembersAPI.as_view()),
    path('HelpDeskAPI/', HelpDeskAPI.as_view()),
    path('AccountingAPI/', AccountingAPI.as_view()),
    path('FlatsAPI/', FlatsAPI.as_view()),
    path('UserAPI/', UserAPI.as_view()),
    path('VehicleAPI/', VehicleAPI.as_view()),
    path('NoticeAPI/', NoticeAPI.as_view()),
    path('ComplaintTypeAPI/', ComplaintTypeAPI.as_view()),
    path('MaintenanceReportAPI/', MaintenanceReportAPI.as_view()),
    path('PurchaseOrderAPI/', PurchaseOrderAPI.as_view()),
    path('PurchaseOrderReportAPI/', PurchaseOrderReportAPI.as_view()),
    path('HelpDeskReportAPI/', HelpDeskReportAPI.as_view()),
    path('NoticeReportAPI/', NoticeReportAPI.as_view()),
]
