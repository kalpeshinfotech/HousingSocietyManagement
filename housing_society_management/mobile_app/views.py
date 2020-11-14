from django.contrib.postgres.aggregates import ArrayAgg
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # <-- Here
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.postgres.aggregates import ArrayAgg
from hsm.society import ResSociety

# Create your views here.
from dashboard.views import (Maintenance, Members, HelpDesk, Accounting, Flats, CurrentUser, Vehicle, Notice,
                             ComplaintType, PurchaseOrder)
from hsm.reports import MaintenanceReport, PurchaseOrderReport, HelpDeskReport, NoticeReport
from django.contrib.auth.models import User


class MaintenanceAPI(APIView):
    # model = Maintenance
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        society_ids = self.request.META.get('HTTP_SOCIETY_ID').split(',')
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = Maintenance().get_data(request, request.user, HTTP_SOCIETY_ID=society_ids)
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class MaintenanceReportAPI(APIView):
    # model = Maintenance
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        print("asfdasdf", request.user.id)
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = MaintenanceReport().get_data(request, request.META.get('HTTP_MAINTENANCE_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class AppToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        society_rec = ResSociety.objects.filter(resflat__flat_owner__user=user).aggregate(
            flat_ids=ArrayAgg('resflat__pk'), society_ids=ArrayAgg('pk', distinct=True))
        return Response(
            {'token': token.key, 'society_id': society_rec['society_ids'], 'flat_ids': society_rec['flat_ids']}
        )


class MembersAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        # society_ids = request.session.get('society_ids')
        # print(society_ids)
        print("This is Meta **************{request.META}")
        data = Members().get_data(request, request.user,
                                  request.META.get('HTTP_SOCIETY_ID'))  # how to assign society instance automatically ?
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class HelpDeskAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = HelpDesk().get_data(request, request.user, request.META.get('HTTP_SOCIETY_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)

    def put(self, request):
        HelpDesk().post(request)
        return Response({'Success': 'Success'})


class AccountingAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = Accounting().get_data(request, request.user.id)
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class FlatsAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        print(request.user.id)
        data = Flats().get_data(request, request.user, request.META.get('HTTP_SOCIETY_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class UserAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        print(request.user)
        data = CurrentUser().get_data(request.user)
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class VehicleAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        print(request.user)
        data = Vehicle().get_data(request.user, request.META.get('HTTP_SOCIETY_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class NoticeAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        print(request.user.id)
        data = Notice().get_data(request, request.user, request.META.get('HTTP_SOCIETY_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class ComplaintTypeAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = ComplaintType().get_data(request)
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class PurchaseOrderAPI(APIView):
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        print(request.user)
        data = PurchaseOrder().get_data(request, request.user, request.META.get('HTTP_SOCIETY_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class PurchaseOrderReportAPI(APIView):
    # model = Maintenance
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        print("asfdasdf", request.user.id)
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = PurchaseOrderReport().get_data(request, request.META.get('HTTP_PURCHASE_ORDER_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class HelpDeskReportAPI(APIView):
    # model = Maintenance
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        print("asfdasdf", request.user.id)
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = HelpDeskReport().get_data(request, request.META.get('HTTP_COMPLAINT_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)


class NoticeReportAPI(APIView):
    # model = Maintenance
    permission_classes = (IsAuthenticated,)  # <-- And here

    def post(self, request, *args, **kwargs):
        print("asfdasdf", request.user.id)
        response = {"is_success": False, "status": 500, "msg": "", "data": []}
        data = NoticeReport().get_data(request, request.META.get('HTTP_NOTICE_ID'))
        if data:
            response.update({"is_success": True, "status": 200, "msg": "", "data": data})
        return Response(response)
