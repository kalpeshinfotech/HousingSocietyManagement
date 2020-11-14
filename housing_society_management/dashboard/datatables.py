from django.db.models import F, Sum, Value, CharField, ExpressionWrapper, Func
from django.db.models.functions import Concat
from django_datatables_view.base_datatable_view import BaseDatatableView

from hsm.account import AccountLine
from hsm.maintenance import Maintenance


class MaintenanceDT(BaseDatatableView):
    model = Maintenance
    columns = ['pk', 'name', 'sub_total', 'total', 'dues']
    order_columns = ['pk', 'name']

    def get_initial_queryset(self):
        qs = self.model.objects.filter(pk__in=self.request.POST.getlist('row[]'))
        self.request.session['maintenance_ids'] = self.request.POST.getlist('row[]')
        return qs.annotate(
            dues=F('total')-F('sub_total')
        )


class MaintenanceServiceDT(BaseDatatableView):
    model = Maintenance
    columns = ['maintenanceline__service__name', 'cost']
    order_columns = ['maintenanceline__service__name']

    def get_initial_queryset(self):
        qs = self.model.objects.filter(pk__in=self.request.POST.getlist('row[]'))
        self.request.session['maintenance_ids'] = self.request.POST.getlist('row[]')
        return qs.values('maintenanceline__service__name').annotate(cost=Sum('maintenanceline__cost')
        )


class AccountLineDT(BaseDatatableView):
    model = AccountLine
    columns = ['pk', 'transaction_no', 'action_type', 'name', 'amount', 'create_date_str', 'holder_name']

    def get_initial_queryset(self):
        print(self.request.GET)
        transaction_id = self.request.GET.get('transaction_id')
        qs = self.model.objects.filter(transaction_id=transaction_id).annotate(
            create_date_str=ExpressionWrapper(
                Func(F('create_date'), Value("DD/MM/YYYY"), function='TO_CHAR'), output_field=CharField()),
            name=F('account__name'),
            balance=F('account__balance'),
            holder_name=Concat('account__respartner__user__first_name', Value(' '), 'account__respartner__user__last_name'),
            transaction_no=F('transaction__number')
        ).order_by('pk')
        return qs