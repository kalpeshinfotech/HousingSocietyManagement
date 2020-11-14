from datetime import datetime

from django.contrib.postgres.indexes import BrinIndex
from django.db import models, transaction
from django.db.models import (Case, CharField, Count, DateTimeField,
                              ExpressionWrapper, F, FloatField, Func, Max, Min,
                              Prefetch, Q, Sum, Value, When, Subquery)
from django.db.models.functions import Concat
from django.utils.html import escape
from django_datatables_view.base_datatable_view import BaseDatatableView
from rest_framework.views import APIView

from hsm.account import AccountLine, PartnerAccount, Transaction
from hsm.society import SocietyServiceLine, ResSociety
from . import account
from . import models as base
from . import society


class Maintenance(base.BaseModel):
    STATE_TYPE_PAID = 'PAID'
    STATE_TYPE_UNPAID = 'UNPAID'
    STATE_TYPE_CONFIRMED = 'CONFIRMED'
    STATE_CHOICES = (
        (STATE_TYPE_PAID, 'PAID'),
        (STATE_TYPE_UNPAID, 'UNPAID'),
        (STATE_TYPE_CONFIRMED, 'CONFIRMED'),
    )
    name = models.CharField(max_length=20, null=True, blank=False)
    flat = models.ForeignKey(society.ResFlat, on_delete=models.PROTECT, null=True)
    # partner = models.ForeignKey(base.ResPartner, on_delete=models.PROTECT, null=True)
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    state = models.CharField(choices=STATE_CHOICES, max_length=10, default=STATE_TYPE_UNPAID)
    paid_date = models.DateField(null=True, blank=True)
    bill_date = models.DateField(auto_now_add=True, null=True)
    transaction = models.ForeignKey(account.Transaction, on_delete=models.PROTECT, null=True)
    sub_total = models.FloatField(default=0, null=True)
    total = models.FloatField(default=0, null=True)

    class Meta:
        db_table = 'maintenance'
        indexes = (
            BrinIndex(fields=['bill_date']),
        )

    def __str__(self):
        return self.name

    def process(self, **kwargs):
        print(kwargs)
        with transaction.atomic():
            transaction_id = kwargs.get('transaction_id')
            asof = kwargs.get('asof')
            user = kwargs.get('user')
            society_ids = kwargs.get('society_id')
            total_amt = 0.0
            society_obj = ResSociety.objects.filter(pk__in=society_ids).values(society_accnt=F('partner__account__id')).first()

            l = []
            mnt_qs = Maintenance.objects.filter(transaction_id=transaction_id, state=Maintenance.STATE_TYPE_CONFIRMED)
            print(mnt_qs)
            if mnt_qs.count() > 0:
                mnt_accnt = mnt_qs.values(
                    'maintenanceline__society_service__id'
                ).annotate(
                    cost=Sum('maintenanceline__cost'),
                    service_accnt=F('maintenanceline__society_service__account__pk')
                )

                for line in mnt_accnt:
                    print("lineline", line)
                    l.append(AccountLine(
                        account_id=line['service_accnt'], amount=line['cost'], action_type=AccountLine.ACTION_TYPE_CREDITED,
                        transaction_id=transaction_id, create_date=asof, write_date=asof, create_user_id=user,
                        write_user_id=user
                    ))
                    total_amt += line['cost']

                # debit from society account
                AccountLine.create(society_obj.get('society_accnt'), total_amt, AccountLine.ACTION_TYPE_DEBITED, transaction_id, asof, user, None)
                PartnerAccount.update_balance(
                    asof, user, partner_id=society_obj.get('society_accnt'), amount=total_amt,
                    action_type=AccountLine.ACTION_TYPE_DEBITED
                )

                # credit to individual account
                AccountLine.objects.bulk_create(l)
                for line in mnt_accnt:
                    PartnerAccount.update_balance(
                        asof, user, partner_id=line['service_accnt'], amount=line['cost'], action_type=AccountLine.ACTION_TYPE_CREDITED
                    )

                # update maintenance state
                mnt_qs.update(state=Maintenance.STATE_TYPE_PAID, write_date=asof, write_user=user)
                # update transaction as complete
                Transaction.objects.select_for_update().filter(pk=transaction_id).update(state=Transaction.STATE_COMPLETED)
            else:
                return False


class MaintenanceLine(base.BaseModel):
    maintenance = models.ForeignKey(Maintenance, on_delete=models.PROTECT, null=True)
    cost = models.FloatField(default=0.0)
    service = models.ForeignKey(society.Service, on_delete=models.PROTECT, null=True)
    society_service = models.ForeignKey(society.SocietyServiceLine, on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'maintenance_lines'


class FlatMaintenanceView(Maintenance):
    class Meta:
        proxy = True
        verbose_name = 'Flat Maintenance Dashboard'
        verbose_name_plural = 'Flat Maintenance Dashboard'


class MaintenanceDataTable(BaseDatatableView):
    model = Maintenance
    columns = ['name', 'flat_number',
               'bill_date_format',
               'paid_date_format',
               'payment_method', 'state', 'total', 'sub_total', 'dues', 'paid', 'unpaid']
    order_columns = columns

    # max_display_length = 2

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        qs = Maintenance.objects.all().annotate(
            amount=Sum('maintenanceline__cost'),
            paid=Sum(F('maintenanceline__cost'), filter=Q(state=Maintenance.STATE_TYPE_PAID)) + (
                    Count('id', filter=Q(
                        flat__society__maintenance_due_days__lt=(datetime.now().date() - F('bill_date')),
                        state=Maintenance.STATE_TYPE_PAID),
                          distinct=True, output_field=FloatField()) * Min(F('flat__society__maintenance_due_charge'))),
            # dues=Count('id', filter=Q(
            # 	flat__society__maintenance_due_days__lt=(datetime.now().date() - F('bill_date'))),
            # 		   distinct=True, output_field=FloatField()) * Min(F('flat__society__maintenance_due_charge')),
            unpaid=Sum(F('maintenanceline__cost'), filter=Q(state=Maintenance.STATE_TYPE_UNPAID)) + (
                    Count('id', filter=Q(
                        flat__society__maintenance_due_days__lt=(datetime.now().date() - F('bill_date')),
                        state=Maintenance.STATE_TYPE_UNPAID),
                          distinct=True, output_field=FloatField()) *
                    Min(F('flat__society__maintenance_due_charge'))),
            payment_method=F('transaction__payment_method'),
            flat_number=Concat('flat__wing__name', Value("-"), 'flat__number', output_field=CharField()),
            bill_date_format=ExpressionWrapper(Func(F('bill_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                               output_field=CharField()),
            paid_date_format=ExpressionWrapper(Func(F('paid_date'), Value("DD MM YYYY"), function='TO_CHAR'),
                                               output_field=CharField()),
            dues=F('total') - F('sub_total')
        )
        #
        # 	# print("ssss", qs.values())
        return qs

# def prepare_results(self, qs):
# 	# prepare list with output column data
# 	# queryset is already paginated here
# 	from .admin import FlatMaintenanceViewAdmin
# 	json_data = []
# 	for item in qs:
# 		json_data.append([
# 			# escape(item.number),  # escape HTML for security reasons
# 			# escape("{0} {1}".format(item.customer_firstname, item.customer_lastname)),
# 			# # escape HTML for security reasons
# 			# item.get_state_display(),
# 			# item.created.strftime("%Y-%m-%d %H:%M:%S"),
# 			# item.modified.strftime("%Y-%m-%d %H:%M:%S")
# 			item.name,
# 			item.flat_number,
# 			item.bill_date_format,
# 			item.paid_date_format,
# 			item.payment_method,
# 			item.state
# 		])
# 	print("json_data", json_data)
# 	return json_data


class MaintenanceLineDataTable(BaseDatatableView):
    model = MaintenanceLine
    columns = ['service_name', 'cost']
    order_columns = columns

    def get_initial_queryset(self):
        MaintenanceLine.objects.filter().annotate(
            service_name=F('service__name')
        )


class MyMaintenanceDatatables(BaseDatatableView):
    model = Maintenance
    columns = ['name', 'flat', 'partner', 'notes', 'state']
    order_columns = ['name', 'flat', 'partner', 'notes', 'state']
