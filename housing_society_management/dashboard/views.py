from datetime import datetime
import json

from braces.views import GroupRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (Case, CharField, Count, DateTimeField,
                              ExpressionWrapper, F, FloatField, Func, Max, Min,
                              Prefetch, Q, Sum, Value, When, Subquery)
from django.db.models.functions import Concat
from django.forms import formset_factory
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView, View

from hsm import maintenance, account
from hsm.account import AccountLine
from hsm.constants import SECRETORY_GROUP
from hsm.forms import PaymentForm
from hsm.helpdesk import Complaint, ComplaintCategory
from hsm.models import ResPartner
from hsm.society import ResFlat, ResSociety
from hsm.utils import TIMEZONE, TO_CHAR
from hsm.society import ResFlat, ResSociety
from rest_framework.authtoken.models import Token


class SecretoryRequiredMinxin(GroupRequiredMixin):
    group_required = SECRETORY_GROUP
    login_url = 'dashboard:login'


class Dashboard(View):
    login_required = False
    dashboard_template = 'dashboard/dashboard.html'
    login_template = 'dashboard/login.html'

    def society_info(self, request):
        society_ids = request.session.get('society_ids')
        print("society", society_ids)
        info = ResSociety.objects.filter(pk__in=society_ids).values('name').annotate(
            flat_allocated=Count('resflat', filter=F('resflat__is_allocated')),
            total_flats=Count('resflat'),
            address=Concat(
                F('partner__street1'), Value(','), F('partner__street2'), Value(','),
                F('partner__city'), Value(','),
                F('partner__state__name'), Value(','), F('partner__country__name'),
                Value(','), F('partner__zip_code'),
                output_field=CharField())
        )[0]
        ctx = {'society': info}
        print(society_ids)
        members = ResPartner.objects.filter(owner_flat__society_id__in=society_ids).count() \
                  + ResPartner.objects.filter(renter_flat__society_id__in=society_ids).count()
        ctx.update({'members': members})
        ctx.update({'owners': ResPartner.objects.filter(owner_flat__society_id__in=society_ids).count()})
        ctx.update({'renters': ResPartner.objects.filter(renter_flat__society_id__in=society_ids).count()})
        from hsm.vehicle import PartnerVehicle
        ctx.update({'vehicles': PartnerVehicle.objects.filter(society__in=society_ids).count()})
        print(ctx)
        return ctx

    def get(self, request, *args, **kwargs):
        if 'logout' in kwargs:
            logout(request)
            return render(request, self.login_template)
        elif request.user.is_authenticated:
            ctx = self.society_info(request)
            return render(request, self.dashboard_template, context=ctx)
        else:
            return render(request, self.login_template)

    def post(self, request, *args, **kwargs) -> render:
        print(kwargs)
        if 'login' in kwargs:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            data = {}
            # if user and user.has_perm('dashboard.view_dashboard'):
            if user:
                a = login(request, user)
                society_rec = ResSociety.objects.filter(resflat__flat_owner__user=request.user).aggregate(
                    flat_ids=ArrayAgg('resflat__pk'), society_ids=ArrayAgg('pk', distinct=True))
                print(society_rec)
                request.session['society_ids'] = society_rec['society_ids']
                request.session['flat_ids'] = society_rec['flat_ids']
                Token.objects.get_or_create(user=user)
                ctx = self.society_info(request)
                return render(request, self.dashboard_template, context=ctx)
        else:
            return render(request, self.login_template)


class DashboardLoginRequiredMixin(LoginRequiredMixin):
    login_url = 'dashboard:login'


class Maintenance(DashboardLoginRequiredMixin, ListView):
    template_name = 'dashboard/table-maintenance.html'
    detailed_template_view = 'dashboard/view-maintenance.html'

    def get_data(self, request, user_id=None, **kwargs):
        qs = maintenance.Maintenance.objects.filter()
        if request.user.groups.filter(name=SECRETORY_GROUP).exists():
            qs = qs.filter(flat__society__pk__in=request.session.get('society_ids') or kwargs.get('HTTP_SOCIETY_ID'))
        else:
            qs = qs.filter(flat__flat_owner__user=user_id)
        if 'filter_date' in kwargs:
            qs = qs.filter(bill_date__gte=request.POST.get('fromDate'), bill_date__lte=request.POST.get('toDate'))
        data = qs.annotate(
            flat_number=Concat('flat__wing__name', Value("-"), 'flat__number', output_field=CharField()),
            payment_method=F('transaction__payment_method'),
            # bill_date_format=ExpressionWrapper(
            #     Func(F('bill_date'), Value("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField()),
            bill_date_format=TO_CHAR(TIMEZONE(Value('IST'), F('bill_date')), Value("DD/MM/YYYY")),
            paid_date_format=ExpressionWrapper(
                Func(F('paid_date'), Value("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField())
        ).values(
            'name',
            'flat_number',
            'bill_date_format',
            'paid_date_format',
            'state', 'payment_method', 'pk'
        ).annotate(
            amount=Sum('sub_total'),
            paid=Sum(F('total'), filter=Q(state=maintenance.Maintenance.STATE_TYPE_PAID)),
            unpaid=Sum(F('total'), filter=Q(state=maintenance.Maintenance.STATE_TYPE_UNPAID)),
            dues=F('total') - F('sub_total'),
        ).order_by(
            F('pk').desc(nulls_last=True)
        )
        return list(data)

    def get(self, request, *args, **kwargs):
        if 'object_id' in kwargs and ResPartner.objects.filter(user=request.user).filter(
                owner_flat__maintenance__id=kwargs['object_id']).count():
            from hsm.reports import MaintenanceReport
            data = MaintenanceReport().get_data(request, maintenance_id=kwargs.get('object_id'))
            template = self.detailed_template_view
            return render(request, template, data)
        else:
            data = self.get_data(request, user_id=request.user.id)
            template = self.template_name
        return render(request, template, {'data': json.dumps(data), 'payment': PaymentForm()})

    def post(self, request, *args, **kwargs):
        if 'maintenance_info' in kwargs:
            from hsm.reports import MaintenanceReport
            data = MaintenanceReport().get_data(request, maintenance_id=kwargs.get('object_id'))
        if 'filterDate' in kwargs:
            data = self.get_data(request, user_id=request.user.id, filter_date='')
            print(data)
            return JsonResponse(data, safe=False)
        return render(request, self.template_name)


class Members(DashboardLoginRequiredMixin, View):
    template_name = 'dashboard/table-members.html'
    detailed_template_view = 'dashboard/view-member-detail.html'
    model = ResPartner

    def get_data(self, request, user_id=None, society_ids=None, **kwargs):
        from hsm.models import ResPartner
        from hsm.society import ResFlat, ResSociety
        # society_ids = ResPartner.objects.filter(user_id=user_id).values_list('society', flat=True)
        data = []
        if 'filter_date' in kwargs:
            data = self.model.objects.filter(society__in=society_ids,
                                             dob__gte=request.POST.get('fromDate'),
                                             dob__lte=request.POST.get('toDate')).values(
                'pk', 'alt_mobile_no', 'mobile_no', 'email'
            ).annotate(
                member_name=Concat('user__first_name', Value(' '), 'user__last_name'),
                dob=ExpressionWrapper(Func(F('dob'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                      output_field=CharField()),
            ).distinct()
            return list(data)

        data = self.model.objects.filter(society__in=society_ids).values(
            'pk', 'alt_mobile_no', 'mobile_no', 'email'
        ).annotate(
            member_name=Concat('user__first_name', Value(' '), 'user__last_name'),
            dob=ExpressionWrapper(Func(F('dob'), Value("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField()),
        ).distinct()

        # for flat in flat_obj:
        #     owners_list = []
        #     if flat.flat_owner.exists():
        #         owners_list = [' '.join([owner.user.first_name, owner.user.last_name]) for owner in flat.flat_owner.all()]
        #     data.append({'wing_name': flat.wing_name, 'society_name': flat.society_name, 'number': flat.number,
        #                  'owners': owners_list})
        return list(data)

    def get(self, request, *args, **kwargs):
        if 'object_id' in kwargs:
            from hsm.reports import MemberDetailReport
            data = MemberDetailReport().get_data(request, member_id=kwargs.get('object_id'))
            template = self.detailed_template_view
            return render(request, template, data)
        society_ids = request.session.get('society_ids')
        data = self.get_data(request, user_id=request.user.id, society_ids=society_ids)
        print(data)
        return render(request, self.template_name, {'data': data})

    def post(self, request, *args, **kwargs):
        if 'filterDate' in kwargs:
            society_ids = request.session.get('society_ids')
            data = self.get_data(request, user_id=request.user.id, society_ids=society_ids, filter_date='')
            return JsonResponse(data, safe=False)
        return render(request, self.template_name)


class HelpDesk(DashboardLoginRequiredMixin, View):
    from .forms import ComplaintForm, ReplyForm
    template_name = 'dashboard/table-helpDesk.html'
    formTemplate = 'dashboard/complaint_form.html'
    form1Template = 'dashboard/reply-complaint.html'
    detailed_template_view = 'dashboard/view-compliant.html'
    form = ComplaintForm
    form1 = ReplyForm

    def get_data(self, request, user_id=None, society_ids=None, **kwargs):
        from hsm.models import ResPartner

        if 'filter_date' in kwargs:
            data = Complaint.objects.filter(create_user_id=user_id,
                                            society__in=society_ids,
                                            create_date__gte=request.POST.get('fromDate'),
                                            create_date__lte=request.POST.get('toDate')
                                            ).values(
                'pk', 'number', 'name', 'status_type', 'reply'
            ).annotate(
                create_date=ExpressionWrapper(Func(F('create_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                              output_field=CharField()),
                complaint_type=F('complaint_type__name')

            ).order_by('-pk')
            return list(data)
        elif request.user.groups.filter(name=SECRETORY_GROUP).exists():
            data = Complaint.objects.filter(society__in=society_ids).values(
                'pk', 'number', 'name', 'status_type', 'reply'
            ).annotate(
                create_date=ExpressionWrapper(Func(F('create_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                              output_field=CharField()),
                complaint_type=F('complaint_type__name')

            ).order_by('-pk')
            return list(data)

        data = Complaint.objects.filter(create_user_id=user_id,
                                        society__in=society_ids).values(
            'pk', 'number', 'name', 'status_type', 'reply'
        ).annotate(
            create_date=ExpressionWrapper(Func(F('create_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                          output_field=CharField()),
            complaint_type=F('complaint_type__name')

        ).order_by('-pk')
        return list(data)

    def get(self, request, *args, **kwargs):
        if 'complaint_form' in kwargs:
            return render(request, self.formTemplate, {'complaint': self.form()})
        elif 'reply_form' in kwargs:
            return render(request, self.form1Template, {'reply': self.form1()})
        elif 'object_id' in kwargs:
            print(Complaint.objects.get(pk=kwargs.get('object_id')))
            from hsm.reports import HelpDeskReport
            data = HelpDeskReport().get_data(request, complaint_id=kwargs.get('object_id'))
            # data = self.get_data(request, user_id=request.user.id)
            template = self.detailed_template_view
            # for data in data:
            #     print(data)
            # print(data)
            return render(request, template, data)
        society_ids = request.session.get('society_ids')
        data = self.get_data(request, user_id=request.user.id, society_ids=society_ids)
        print(request.session.get('society_ids')[0])
        # print(data)
        return render(request, self.template_name, {'data': json.dumps(data)})

    def post(self, request, *args, **kwargs):
        if 'filterDate' in kwargs:
            data = self.get_data(request, user_id=request.user.id, filter_date='')
            return JsonResponse(data, safe=False)
        form = self.ComplaintForm(request.POST, request.FILES)
        form1 = self.ReplyForm(request.POST)
        # print(form1)
        # print(form1.is_valid())
        # print(form.is_valid())
        # print(form)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            complaint = form.cleaned_data.get('complaint_type')
            comment = form.cleaned_data.get('comment')
            upload_file = form.cleaned_data.get('upload_file')
            status = Complaint.STATUS_SUBMITTED
            society = request.session.get('society_ids')[0]
            Complaint.objects.create(
                name=name, complaint_type=complaint, comment=comment, status_type=status,
                society_id=society, upload_file=upload_file, create_user=request.user, write_user=request.user)
        if form1.is_valid():
            status = form1.cleaned_data.get('status_type')
            reply = form1.cleaned_data.get('reply')
            Complaint.objects.filter(pk=kwargs.get('object_id')).update(status_type=status, reply=reply)
        return redirect(to='dashboard:complaint_table')


# code for reply is remaining

class Accounting(DashboardLoginRequiredMixin, View):
    template_name = 'dashboard/table-accounting.html'

    def get_data(self, request, user_id):
        data = {}
        qs = AccountLine.objects
        if request.user.groups.filter(name=SECRETORY_GROUP).exists():
            print(request.session.get('society_ids'))
            qs = qs.filter(society__id__in=request.session.get('society_ids'))
        else:
            qs = qs.filter(account__respartner__user__id=user_id)

        lines = AccountLine.objects.filter(transaction_id__in=Subquery(qs.values('transaction_id')))
        data = lines.values('pk', 'amount', 'action_type').annotate(
            create_date=ExpressionWrapper(Func(F('create_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                          output_field=CharField()),
            payment_type=F('transaction__payment_method'),
            name=F('account__name'),
            balance=F('account__balance'),
            # holder_name=Concat('account__partner__user__first_name', Value(' '), 'account__partner__user__last_name')
            holder_name=F('transaction__number')
        ).order_by('-create_date', 'pk')
        return json.dumps(list(data))

    def get(self, request, *args, **kwargs):
        data = self.get_data(request, user_id=request.user.id)
        return render(request, self.template_name, {'data': data})


class Flats(DashboardLoginRequiredMixin, View):
    template_name = 'dashboard/table-flats.html'
    detailed_template_view = 'dashboard/view-member-detail.html'
    model = ResFlat

    def get_data(self, request, user_id=None, society_ids=None, **kwargs):
        flats = []
        # society_ids = request.session.get('society_ids')
        if 'filter_date' in kwargs:
            data = self.model.objects.filter(society_id__in=society_ids,
                                             registration_date__gte=request.POST.get('fromDate'),
                                             registration_date__lte=request.POST.get('toDate')
                                             ).annotate(
                registration_date_str=ExpressionWrapper(
                    Func(F('registration_date'), Value("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField()),
                wing_str=F('wing__name'),
                is_allocated_str=Case(When(is_allocated=True, then=Value('Yes')), default=Value('No'),
                                      output_field=CharField())
            ).prefetch_related('flat_owner__user')

            for rec in data:
                flats.append({
                    'pk': rec.pk, 'number': rec.number, 'area': rec.area,
                    'registration_number': rec.registration_number,
                    'registration_date': rec.registration_date_str, 'wing': rec.wing_str,
                    'is_allocated': rec.is_allocated_str,
                    'owner': '<br>'.join([owner.user.get_full_name() for owner in rec.flat_owner.all()]),
                    'renter': '<br>'.join([renter.user.get_full_name() for renter in rec.flat_renter.all()])
                })
            return flats

        data = self.model.objects.filter(society_id__in=society_ids).annotate(
            registration_date_str=ExpressionWrapper(
                Func(F('registration_date'), Value("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField()),
            wing_str=F('wing__name'),
            is_allocated_str=Case(When(is_allocated=True, then=Value('Yes')), default=Value('No'),
                                  output_field=CharField())
        ).prefetch_related('flat_owner__user')

        print(data)

        for rec in data:
            flats.append({
                'pk': rec.pk, 'number': rec.number, 'area': rec.area, 'registration_number': rec.registration_number,
                'registration_date': rec.registration_date_str, 'wing': rec.wing_str,
                'is_allocated': rec.is_allocated_str,
                'owner': '<br>'.join([owner.user.get_full_name() for owner in rec.flat_owner.all()]),
                'renter': '<br>'.join([renter.user.get_full_name() for renter in rec.flat_renter.all()])
            })
            print(flats)
        return flats

    def get(self, request, *args, **kwargs):
        if 'object_id' in kwargs:
            from hsm.reports import MemberDetailReport
            data = MemberDetailReport().get_data(request, member_id=kwargs.get('object_id'))
            template = self.detailed_template_view
            return render(request, template, data)
        society_ids = request.session.get('society_ids')
        print(society_ids)
        data = self.get_data(request, user_id=request.user.id, society_ids=society_ids)
        return render(request, self.template_name, {'data': data})

    def post(self, request, *args, **kwargs):
        if 'filterDate' in kwargs:
            society_ids = request.session.get('society_ids')
            data = self.get_data(request, user_id=request.user.id, society_ids=society_ids, filter_date='')
            return JsonResponse(data, safe=False)
        return render(request, self.template_name)


class Transactions(SecretoryRequiredMinxin, View):
    model = account.Transaction
    template_name = 'dashboard/table-transactions.html'

    def get_data(self, request, user_id):
        from hsm.utils import TO_CHAR, TIMEZONE
        society_ids = request.session.get('society_ids')
        data = self.model.objects.filter(accountline__society_id__in=society_ids).values(
            'pk', 'amount', 'payment_method', 'number', 'reference', 'state').annotate(
            create_date=TO_CHAR(TIMEZONE(Value('IST'), F('create_date')), Value('YYYY/MM/DD HH:MI:SS'))
        ).distinct().order_by('-pk')
        return list(data)

    def get(self, request, *args, **kwargs):
        data = list(self.get_data(request, user_id=request.user.id))
        print(data)
        return render(request, self.template_name, context={'data': json.dumps(data)})

    def post(self, request, *args, **kwargs):
        print(request.POST)
        if 'register_payment' in kwargs:
            asof = datetime.now()
            society_id = request.session.get('society_ids')
            print(society_id)
            maintenance.Maintenance().process(
                transaction_id=request.POST.get('transaction_id'), asof=asof, user=request.user.id,
                society_id=request.session.get('society_ids')
            )
        return JsonResponse({'is_success': True}, status=200)


class AcccountLine(SecretoryRequiredMinxin, View):
    model = account.AccountLine


class Profile(DashboardLoginRequiredMixin, View):
    template_name = 'dashboard/profile.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name)


class Notice(DashboardLoginRequiredMixin, View):
    from .forms import NoticeForm
    from hsm.society import Notice
    template_name = 'dashboard/table-notice.html'
    formTemplate = 'dashboard/add_notice.html'
    detailed_template_view = 'dashboard/notice.html'
    form = NoticeForm()
    model = Notice

    def get_data(self, request, user_id=None, society_ids=None, **kwargs):
        if 'filter_date' in kwargs:
            data = self.model.objects.filter(society_id__in=society_ids,
                                             date__gte=request.POST.get('fromDate'),
                                             date__lte=request.POST.get('toDate')
                                             ).values('pk', 'title').annotate(
                notice_date=ExpressionWrapper(Func(F('date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                              output_field=CharField()), )
            print(data)
            return list(data)
        data = self.model.objects.filter(society_id__in=society_ids).order_by("-date").values(
            'pk', 'title',
        ).annotate(notice_date=ExpressionWrapper(Func(F('date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                                 output_field=CharField()), )
        print(data)
        return list(data)

    def get(self, request, *args, **kwargs):
        society_ids = request.session.get('society_ids')
        print(kwargs)
        if 'add_notice' in kwargs:
            return render(request, self.formTemplate, {'add_notice': self.form})

        elif 'object_id' in kwargs:
            from hsm.reports import NoticeReport
            data = NoticeReport().get_data(request, notice_id=kwargs.get('object_id'))
            template = self.detailed_template_view
            return render(request, template, data)

        data = self.get_data(request, user_id=request.user.id, society_ids=society_ids)
        return render(request, self.template_name, {'data': data})

    def post(self, request, *args, **kwargs):
        if 'filterDate' in kwargs:
            print('Yes requested')
            society_ids = request.session.get('society_ids')
            data = self.get_data(request, user_id=request.user.id, society_ids=society_ids, filter_date='')
            return JsonResponse(data, safe=False)
        from .forms import NoticeForm
        if request.method == 'POST':
            form = NoticeForm(request.POST)
            if form.is_valid():
                title = form.cleaned_data.get('title')
                description = form.cleaned_data.get('description')
                society = request.session.get('society_ids')[0]
                self.model(
                    title=title, description=description, create_user=request.user, write_user=request.user,
                    society_id=society
                ).save()
        return redirect(to='dashboard:my_notices')


class CurrentUser(DashboardLoginRequiredMixin, View):
    def get_data(self, user_id):
        data = {}
        data = User.objects.filter(username=user_id).values('id', 'username', 'password', 'first_name', 'last_name')
        print(data)
        return list(data)


class ComplaintType(DashboardLoginRequiredMixin, View):
    def get_data(self, request):
        data = {}
        data = ComplaintCategory.objects.all().values('id', 'name', 'description')
        print(data)
        return list(data)


class Vehicle(DashboardLoginRequiredMixin, View):
    from hsm.vehicle import PartnerVehicle
    template_name = 'dashboard/table-vehicle.html'
    model = PartnerVehicle

    def get_data(self, user_id=None, society_ids=None):
        data = self.model.objects.filter(society__in=society_ids).values('vehicle', 'registration_number').annotate(
            owner=F('owner__name'),
        )
        return list(data)

    def get(self, request, *args, **kwargs):
        society_ids = request.session.get('society_ids')
        data = self.get_data(user_id=request.user.id, society_ids=society_ids)
        print(data)
        return render(request, self.template_name, {'data': json.dumps(data)})


class PurchaseOrder(DashboardLoginRequiredMixin, ListView):
    from .forms import PurchaseForm, PurchaseLineForm, PurchaseLineFormSet, PurchaseLineFormSetData
    from hsm.purchase import PurchaseOrder, PurchaseOrderLine

    template_name = 'dashboard/table-purchase-order.html'
    formTemplate = 'dashboard/purchase_order_build.html'
    model = PurchaseOrder
    detailed_template_view = 'dashboard/view-purchase.html'
    purchaseForm = PurchaseForm

    # purchaseLineForm = PurchaseLineFormSet

    def get_data(self, request, user_id=None, society_ids=None, **kwargs):
        qs = self.model.objects.filter(society_id__in=society_ids)
        if 'filter_date' in kwargs:
            qs = qs.filter(
                order_date__gte=request.POST.get('fromDate'),
                order_date__lte=request.POST.get('toDate')
            )
        data = qs.values('pk', 'number').annotate(
            vendor=F('vendor__name'),
            date=ExpressionWrapper(Func(F('order_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                   output_field=CharField()),
            grand_total=ExpressionWrapper(
                F('grand_total'), output_field=FloatField())
        ).order_by('-pk')
        return list(data)

    def get(self, request, *args, **kwargs):
        if 'purchase_order_maker' and 'purchase_order_lines' in kwargs:
            return render(request, self.formTemplate,
                          {'purchase_order_maker': self.purchaseForm(),
                           'purchase_order_lines': self.PurchaseLineFormSetData})

        elif 'object_id' in kwargs:
            from hsm.reports import PurchaseOrderReport,  MemberDetailReport
            print(MemberDetailReport().get_data(request, member_id=5))
            data = PurchaseOrderReport().get_data(request, purchase_order_id=kwargs.get('object_id'))
            template = self.detailed_template_view
            return render(request, template, data)

        society_ids = request.session.get('society_ids')
        data = self.get_data(request, user_id=request.user.id, society_ids=society_ids)
        print(data)
        return render(request, self.template_name, {'data': data})

    def post(self, request, *args, **kwargs):
        if 'filterDate' in kwargs:
            print("Yes you requested date filter")
            society_ids = request.session.get('society_ids')
            data = self.get_data(request, user_id=request.user.id, society_ids=society_ids, filter_date='')
            return JsonResponse(data, safe=False)

        from .forms import PurchaseForm, PurchaseLineFormSet
        from hsm.purchase import PurchaseOrder, PurchaseOrderLine

        purchaseForm = PurchaseForm(request.POST)
        purchaseLineFormSet = PurchaseLineFormSet(request.POST)

        if purchaseForm.is_valid() and purchaseLineFormSet.is_valid():
            order_date = purchaseForm.cleaned_data.get('order_date')
            number = purchaseForm.cleaned_data.get('number')
            society = request.session.get('society_ids')[0]
            vendor = purchaseForm.cleaned_data.get('vendor')
            notes = purchaseForm.cleaned_data.get('notes')

            po_obj = PurchaseOrder.objects.create(
                order_date=order_date, number=number,
                society_id=society, vendor=vendor,
                notes=notes,
                grand_total=sum(map(lambda x: x.cleaned_data.get('unit_price') * x.cleaned_data.get('quantity'),
                                    purchaseLineFormSet))
            )
            lines = []
            for pol_form in purchaseLineFormSet:
                lines.append(PurchaseOrderLine(**pol_form.cleaned_data, purchase_id=po_obj.pk))
            PurchaseOrderLine.objects.bulk_create(lines)
            return redirect(to='dashboard:purchase_order_table')
        else:
            redirect(to='dashboard:purchase_order_maker')
