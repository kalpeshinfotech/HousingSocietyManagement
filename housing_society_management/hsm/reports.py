from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import CharField, ExpressionWrapper, F, Func, Prefetch, Q
from django.db.models import Value as V
from django.db.models.functions import Cast, Concat
from django.shortcuts import redirect
from num2words import num2words
from wkhtmltopdf.views import PDFTemplateResponse, PDFTemplateView

from hsm import purchase
from hsm.templatetags.hsm_tags import is_secretory

from . import models as base
from . import society
from .maintenance import Maintenance, MaintenanceLine
from .models import ResPartner
from .society import ResFlat
from .helpdesk import Complaint
from .society import Notice, ResFlat
from .models import ResPartner
from .vehicle import PartnerVehicle


class MaintenanceReport(PDFTemplateView):
    filename = 'maintenance.pdf'
    template_name = 'reports/maintenance.html'
    cmd_options = {
        'margin-top': 3,
    }

    def get_data(self, request, maintenance_id=None):
        data = {}
        is_secretory(request.user)
        is_valid = ResPartner.objects.filter(user=request.user).filter(
            owner_flat__maintenance__id=maintenance_id).count()
        if is_valid or request.user.is_superuser:
            maintenance_lines = MaintenanceLine.objects.annotate(service_name=F('service__name'))

            record = Maintenance.objects.filter(pk=maintenance_id).annotate(
                society_address=Concat(
                    F('flat__society__partner__street1'), V(','), F('flat__society__partner__street2'), V(','),
                    F('flat__society__partner__city'), V(','),
                    F('flat__society__partner__state__name'), V(','), F('flat__society__partner__country__name'),
                    V(','), F('flat__society__partner__zip_code'),
                    output_field=CharField()),
                society_name=F('flat__society__name'),
                maintenance_name=F('name'),
                flat_number=Concat(F('flat__wing__name'), V('-'), F('flat__number'), output_field=CharField()),
                flat_owner=F('flat__flat_owner__name'),

            ).prefetch_related('flat__flat_owner',
                               Prefetch('maintenanceline_set', queryset=maintenance_lines, to_attr='maintenance_lines')
                               )

            for each in record:
                data.update({
                    'society_name': each.society_name,
                    'society_address': each.society_address,
                    'maintenance_name': each.maintenance_name,
                    'bill_date': each.bill_date,
                    'paid_date': each.paid_date,
                    'sub_total': each.sub_total,
                    'total': each.total,
                    'pk': each.pk,
                    'flat_number': each.flat_number,
                    'flat_owner': ', '.join([owner.user.get_full_name() for owner in each.flat.flat_owner.all()]),
                    'maintenance_lines': [{'service_name': line.service_name, 'cost': line.cost} for line in
                                          each.maintenance_lines]
                })

            total_in_word = data.get('total') and num2words(data.get('total'), lang='en_IN') or ''
            data.update({'total_in_word': total_in_word})
        return data

    def get(self, request, *args, **kwargs):
        maintenance_id = kwargs.get('object_id')
        response = redirect(to='dashboard:dashboard')
        context = self.get_data(request, maintenance_id=maintenance_id)

        if context:
            maintenance_file_name = Maintenance.objects.filter(pk=maintenance_id).annotate(
                maintenance_file_name=Concat(
                    F('flat__society__name'), V('_'),
                    F('flat__wing__name'), V('-'),
                    F('flat__number'), V('_'),
                    F('name'), V('.pdf'), output_field=CharField()),
            ).values_list('maintenance_file_name', flat=True).first()
            response = PDFTemplateResponse(request=request,
                                           template=self.template_name,
                                           filename=maintenance_file_name,
                                           context=context,
                                           show_content_in_browser=False,
                                           cmd_options={'margin-top': 50, },
                                           )
            print("response", response)
        return response


class PurchaseOrderReport(PDFTemplateView):
    filename = 'PurchaseOrder.pdf'
    template_name = 'purchase_order/PurchaseOrder.html'
    cmd_options = {
        'margin-top': 3,
    }

    def get_data(self, request, purchase_order_id=None):
        data = {}
        purchase_order_lines = purchase.PurchaseOrderLine.objects.annotate(product_name=F('product__name'))
        record = purchase.PurchaseOrder.objects.filter(pk=purchase_order_id).annotate(
            po_date=ExpressionWrapper(Func(F('order_date'), V("DD/MM/YYYY"), function='TO_CHAR'),
                                      output_field=CharField()),
            society_name=F('society__name'),
            society_address=Concat(
                F('society__partner__street1'), V(','), F('society__partner__street2'), V(','),
                F('society__partner__city'), V(','),
                F('society__partner__state__name'), V(','), F('society__partner__country__name'),
                V(','), F('society__partner__zip_code'),
                output_field=CharField()),
            vendor_name=F('vendor__name'),
            vendor_address=Concat(
                F('vendor__street1'), V(','), F('vendor__street2'), V(',\n '),
                F('vendor__city'), V(','), F('vendor__zip_code'), V(',\n '),
                F('vendor__state__name'), V(','), F('vendor__country__name'), V(',\n '),
                F('vendor__mobile_no'), V(',\n '), F('vendor__email'),
                output_field=CharField()),

        ).prefetch_related(Prefetch('purchaseorderline_set', queryset=purchase_order_lines,
                                    to_attr='purchase_order_lines'))

        for each in record:
            data.update({
                'society_name': each.society_name,
                'society_address': each.society_address,
                'vendor_name': each.vendor_name,
                'vendor_address': each.vendor_address,
                'number': each.number,
                'po_date': each.po_date,
                'grand_total': each.grand_total,
                'notes': each.notes,
                'pk': each.pk,
                'purchase_order_lines': [{'product_name': line.product_name,
                                          'quantity': line.quantity,
                                          'unit_price': line.unit_price} for line in
                                         each.purchase_order_lines]
            })
            print(data)
        return data

    def get(self, request, *args, **kwargs):
        purchase_order_id = kwargs.get('object_id')
        response = redirect(to='dashboard:dashboard')
        context = self.get_data(request, purchase_order_id=purchase_order_id)

        if context:
            Purchase_order_file_name = purchase.PurchaseOrder.objects.filter(pk=purchase_order_id).annotate(
                Purchase_order_file_name=Concat(
                    F('society__name'), V('_'),
                    F('vendor__name'), V('-'),
                    F('order_date'), V('.pdf'), output_field=CharField()),
            ).values_list('Purchase_order_file_name', flat=True).first()
            print("file_name", Purchase_order_file_name)
            response = PDFTemplateResponse(request=request,
                                           template=self.template_name,
                                           filename=Purchase_order_file_name,
                                           context=context,
                                           show_content_in_browser=False,
                                           cmd_options={'margin-top': 50, },
                                           )
            print("response", response)
        return response


class HelpDeskReport(PDFTemplateView):
    filename = 'Complaint.pdf'
    template_name = 'HelpDesk/helpdesk.html'
    cmd_options = {
        'margin-top': 3,
    }

    def get_data(self, request, complaint_id=None):
        data = {}
        record = Complaint.objects.filter(pk=complaint_id).annotate(
            complaint_username=F('create_user__first_name'),
            compliant_ticket_no=F('number'),
            compliant_subject=F('name'),
            compliant_comment=F('comment'),
            compliant_current_status=F('status_type'),
            compliant_reply=F('reply'),
            compliant_date=ExpressionWrapper(Func(F('create_date'), V("DD/MM/YYYY"), function='TO_CHAR'),
                                             output_field=CharField()),
            user_complaint_type=F('complaint_type__name'),
            compliant_upload_file=F('upload_file')
        )

        for each in record:
            data.update({
                'pk': each.pk,
                'complaint_username': each.complaint_username,
                'compliant_ticket_no': each.compliant_ticket_no,
                'compliant_current_status': each.compliant_current_status,
                'compliant_subject': each.compliant_subject,
                'compliant_comment': each.compliant_comment,
                'compliant_reply': each.compliant_reply,
                'compliant_date': each.compliant_date,
                'user_complaint_type': each.user_complaint_type,
                'compliant_upload_file': each.compliant_upload_file,
            })
            print(data)
        return data

    def get(self, request, *args, **kwargs):
        complaint_id = kwargs.get('object_id')
        response = redirect(to='dashboard:dashboard')
        context = self.get_data(request, complaint_id=complaint_id)

        if context:
            Complaint_file_name = Complaint.objects.filter(pk=complaint_id).annotate(
                Complaint_file_name=Concat(
                    F('number'), V('_'),
                    F('name'), V('-'),
                    F('create_date'), V('.pdf'), output_field=CharField()),
            ).values_list('Complaint_file_name', flat=True).first()
            print("file_name", Complaint_file_name)
            response = PDFTemplateResponse(request=request,
                                           template=self.template_name,
                                           filename=Complaint_file_name,
                                           context=context,
                                           show_content_in_browser=False,
                                           cmd_options={'margin-top': 50, },
                                           )
            print("response", response)
        return response


class NoticeReport:

    def get_data(self, request, notice_id=None):
        data = {}
        record = Notice.objects.filter(pk=notice_id).annotate(
            notice_title=F('title'),
            notice_description=F('description'),
            notice_date=ExpressionWrapper(Func(F('date'), V("DD/MM/YYYY"), function='TO_CHAR'),
                                          output_field=CharField()),
        )
        print(record)

        for each in record:
            data.update({
                'pk': each.pk,
                'notice_title': each.notice_title,
                'notice_description': each.notice_description,
                'notice_date': each.notice_date,
            })
            print(data)
        return data


class MemberDetailReport:
    def get_data(self, request, member_id=None):
        data = {}
        Member = ResPartner.objects.filter(pk=member_id).annotate(
            member_name=Concat('user__first_name', V(' '), 'user__last_name'),
            member_dob=ExpressionWrapper(Func(F('dob'), V("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField()),
            member_society=F('society__name'),
            member_address=Concat(
                F('street1'), V(','), F('street2'), V(','),
                F('city'), V(','), F('state__name'), V(','), F('country__name'),
                V(','), F('zip_code'), V(',\n '), V('mobile no : '), F('mobile_no'), V(',\n '), V('email : '), F('email'),
                output_field=CharField()),
        )

        Vehicle = PartnerVehicle.objects.filter(owner_id=member_id).annotate(
            member_vehicle=F('vehicle'),
            member_vehicle_registration_no=F('registration_number'),
        )

        Flat = ResFlat.objects.filter(flat_owner=member_id).annotate(
            member_flat_no=Concat(F('wing__name'), V('-'), F('number'), output_field=CharField()),
            member_registration_date=ExpressionWrapper(
                Func(F('registration_date'), V("DD/MM/YYYY"), function='TO_CHAR'),
                output_field=CharField()),
            member_registration_no=F('registration_number'),
            member_flat_renter=F('flat_renter__name'),
        )

        for each in Member:
            data.update({
                'pk': each.pk,
                'member_name': each.member_name,
                'member_dob': each.member_dob,
                'member_society': each.member_society,
                'member_address': each.member_address,
            })

        for each in Vehicle:
            data.update({
                'member_vehicle': each.member_vehicle,
                'member_vehicle_registration_no': each.member_vehicle_registration_no,
            })

        for each in Flat:
            data.update({
                'member_flat_no': each.member_flat_no,
                'member_registration_date': each.member_registration_date,
                'member_registration_no': each.member_registration_no,
                'member_flat_renter': each.member_flat_renter,
            })

        return data
