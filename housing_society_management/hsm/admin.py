from datetime import datetime

from ajax_select import admin as ajax_admin
from ajax_select import fields as ajax_select_fields
from ajax_select import make_ajax_form
from django.contrib import admin, messages
from django.contrib.admin.filters import AllValuesFieldListFilter
from django.contrib.admin.utils import flatten_fieldsets, unquote
from django.db.models import (Case, CharField, Count, DateTimeField,
                              ExpressionWrapper, F, FloatField, Func, Max, Min,
                              Prefetch, Q, Sum, Value, When)
from django.db.models.functions import Cast, Coalesce, Concat
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.functional import curry
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from psycopg2.extras import DictCursor

from . import account, forms, helpdesk, maintenance
from . import models as base
from . import reports, society, vehicle
# from .attendance import Job, SocietyEmployeeDetail
from .purchase import PurchaseOrder, PurchaseOrderLine, Product, Vendor, ProductCategory
from . import POreports

admin.site.site_header = 'Housing Society Management'
admin.site.site_title = 'Housing Society Management'
admin.site.index_title = 'Housing Society Management Administration'


class BaseAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        # models.IntegerField: {'widget': NumberInput(attrs={'size': '20'})},
        # models.ForeignKey: {'widget': Select(attrs={'style': 'width:187px'})},
        # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
        # models.ManyToManyField: {'widget': SelectMultiple(attrs={'size': '5', 'style': 'color:blue;width:100px'})},

    }

    def save_model(self, request, obj, form, change):
        if obj._state.adding:
            obj.create_user = request.user
        obj.write_user = request.user
        obj.write_date = timezone.now()
        super(BaseAdmin, self).save_model(request, obj, form, change)


# def get_form(self, request, obj=None, **kwargs):
# 	form = super(BaseAdmin, self).get_form(request, obj, **kwargs)
#
# 	ajax_select_fields.autoselect_fields_check_can_add(form, self.model, request.user)
# 	return form


@admin.register(society.ResFlat)
class ResFlatAdmin(BaseAdmin):
    list_display = ['number', 'wing', 'society', 'owners', 'renters', 'registration_number', 'is_allocated',
                    'is_active']
    list_select_related = ['society', 'wing']
    list_filter = ['society', 'is_allocated', 'is_active']
    search_fields = ['society__name', 'registration_number']
    filter_horizontal = ['flat_owner', 'flat_renter']

    fieldsets = [
        ('Flat Information', {'fields': (
            ('number',),
            ('wing', 'society'),
            ('area', 'registration_number', 'registration_date'),
            ('is_allocated', 'is_active')), }),
        ('Owner/Renter Information', {'fields': (('flat_owner', 'flat_renter',),)})
    ]

    class Media:
        # css = {"all": ("app_name/css/job_run.css",)}
        js = ("hsm/js/DjangoAjax.js",)

    change_form_template = 'admin/society/res_flat_change_form.html'

    society = None

    def owners(self, obj):
        owners = '<br>'.join([owner.user.get_full_name() for owner in obj.flat_owner.all()])

        return format_html(owners)

    def renters(self, obj):
        renters = '<br>'.join([renter.user.get_full_name() for renter in obj.flat_renter.all()])

        return format_html(renters)

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            self.society = obj.society
        return super(ResFlatAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ['flat_owner', 'flat_renter']:
            kwargs["queryset"] = base.ResPartner.objects.filter(partner_type__name='Individual', society=self.society)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        res = super(ResFlatAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if request.user.is_superuser:
            return res
        # if db_field.name == 'society':
        # 	kwargs["queryset"] = society.ResPartnerSociety.objects.filter(partner_type__name='society')
        # if db_field.name == 'wing':
        # 	kwargs["queryset"] = None
        return res

    def get_queryset(self, request):
        res = super(ResFlatAdmin, self).get_queryset(request)
        res = res.prefetch_related('flat_owner__user')
        if request.user.is_superuser:
            return res
        res = res.filter(Q(flat_owner__user=request.user) | Q(flat_renter__user=request.user))
        return res

    def view_maintenance(self, request, object_id, extra_context=None):
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)

        # Then get the history for this object.
        opts = model._meta
        app_label = opts.app_label

        context = {
            **self.admin_site.each_context(request),
            'title': _('Maintenance: %s') % obj,
            'module_name': str(capfirst(opts.verbose_name_plural)),
            'object': obj,
            'opts': opts,
            'preserved_filters': self.get_preserved_filters(request),
            **(extra_context or {}),
        }
        request.current_app = self.admin_site.name

        return TemplateResponse(request, 'admin/society/flat_maintenance.html', context)


@admin.register(base.ResPartner)
class ResPartnerAdmin(BaseAdmin, ajax_admin.AjaxSelectAdmin):
    list_display = ['name', 'partner_type', 'account', 'is_active', ]
    list_select_related = ['account']
    list_filter = ['is_active', 'partner_type', 'society']
    search_fields = ['name']
    filter_horizontal = ['partner_post_rel', 'society']
    fieldsets = [
        ('User Information', {'fields': (
            ('name', 'dob'),
            ('mobile_no', 'alt_mobile_no', 'email',),
            ('street1', 'street2', 'city', 'zip_code'),
            ('state', 'country'),
            ('partner_type', 'user', 'is_active',),
            ('account',),
        )},),
        ('Societies', {'fields': (('society', 'partner_post_rel'),)}),
        # ('Flats', {'fields': ('owner_flat', )})
    ]
    # form = make_ajax_form(society.ResPartnerSociety, {
    # 	# fieldname: channel_name
    # 	'partner_post_rel': 'partner_post_look',
    # 	'society': 'society_look'
    # })
    readonly_fields = ('partner_type', 'user',)

    change_form_template = 'admin/society/res_partner_change_form.html'

    class Meta:
        proxy = True

    def get_societies(self, obj):
        print(obj.society.all().values_list('name', flat=True))
        return ','.join([s for s in obj.society.all().values_list('name', flat=True)])

    def get_queryset(self, request):
        res = super(ResPartnerAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return res
        res = res.filter(user=request.user)
        return res


class SocietyServiceAdminInline(admin.TabularInline):
    model = society.SocietyServiceLine
    extra = 1
    fields = ['service_type', 'price', 'account']


@admin.register(society.ResSociety)
class ResSocietyAdmin(BaseAdmin):
    list_display = ['name', 'get_wings', 'is_active', ]
    # list_select_related = ['society_wing_rel__name']
    list_filter = ['is_active']
    readonly_fields = ['partner']
    search_fields = ['name']
    filter_horizontal = ['society_wing_rel']
    inlines = [SocietyServiceAdminInline]

    fieldsets = [
        ('Basic Information', {'fields': (
            ('name', 'is_active'),
            ('registration_number', 'partner'),
        ), }),
        ('Maintenance setting', {'fields': ('maintenance_due_days', 'maintenance_due_charge')}),
        ('Wing(s)', {'fields': (('society_wing_rel',),)}),
        # ('Maintenance', {'fields': (('MaintenanceAdminInline',),)}),
    ]

    class Meta:
        proxy = True

    def get_wings(self, obj):
        return ','.join([s.name for s in obj.society_wing_rel.all()])

    def get_queryset(self, request):
        queryset = super(ResSocietyAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related('society_wing_rel')
        if request.user.is_superuser:
            return queryset
        queryset = queryset.filter(partner__user=request.user)
        return queryset


class MaintenanceLineAdmin(admin.TabularInline):
    model = maintenance.MaintenanceLine
    extra = 1
    fields = ['service', 'society_service', 'cost']


# def get_formset(self, request, obj=None, **kwargs):
# 	"""
# 	Pre-populating formset using GET params
# 	"""
# 	print("from django.utils.functional import curry")
# 	initial = []
# 	if request.method == "GET":
# 		#
# 		# Populate initial based on request
# 		#
# 		initial.append({'cost': 300,})
# 		initial.append({'cost': 300,})
# 	formset = super(MaintenanceLineAdmin, self).get_formset(request, obj, **kwargs)
# 	formset.__init__ = curry(formset.__init__, initial=initial)
# 	return formset


@admin.register(maintenance.Maintenance)
class MaintenanceAdmin(BaseAdmin):
    list_display = ['name', 'get_detail_flat', 'get_flat_owner', 'state', 'sub_total', 'total', 'bill_date',
                    'paid_date', 'download_maintenance']
    list_select_related = ['flat', ]
    # list_select_related = ['partner']
    inlines = [MaintenanceLineAdmin]
    readonly_fields = ['transaction', 'bill_date', 'paid_date', 'state', 'sub_total', 'total']
    search_fields = ['name']

    list_filter = ['flat__society', 'is_active']
    change_form_template = 'admin/society/res_partner_change_form.html'

    fieldsets = [
        ('Basic Information', {'fields': (
            ('name', 'is_active'),
            ('flat',),
            ('bill_date', 'paid_date', 'state'),
            ('transaction', 'sub_total', 'total'),
            ('notes',),
        ), }),
        # ('Wing(s)', {'fields': (('MaintenanceAdminInline',),)}),
        # ('Maintenance', {'fields': (('MaintenanceAdminInline',),)}),
    ]

    def download_maintenance(self, obj):
        return format_html(
            '<a class="button" href="{}">Download</a>',
            reverse('admin:maintenance_pdf', args=[obj.pk]),
        )

    def get_detail_flat(self, obj):
        return ''.join([obj.flat.wing.name, '-', str(obj.flat.number)])

    def get_flat_owner(self, obj):
        return format_html('<br>'.join([owner.user.get_full_name() for owner in obj.flat.flat_owner.all()]))

    def get_queryset(self, request):
        queryset = super(MaintenanceAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related('flat__wing', 'flat__flat_owner')
        return queryset

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields

        if self.declared_fieldsets:
            return flatten_fieldsets(self.declared_fieldsets)
        else:
            return list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]
            ))

    def valid_maintenance_payment(self, queryset):
        msg, status = '', True
        if queryset.values('flat_id').order_by('flat_id').distinct('flat_id').count() > 1:
            msg = 'Please select same Flat'
            status = False

        if maintenance.Maintenance.STATE_TYPE_PAID in queryset.values_list('state', flat=True).order_by(
                'state').distinct('state'):
            msg = 'Already Paid for selected Maintenance'
            status = False
        return msg, status

    def make_payment(self, request, queryset, *args, **kwargs):
        msg, status = self.valid_maintenance_payment(queryset)

        if not status:
            self.message_user(request, msg, messages.WARNING)
            return HttpResponseRedirect(reverse('admin:hsm_maintenance_changelist'))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['module_name'] = str(capfirst(self.model._meta.verbose_name_plural))
        context['title'] = 'Maintenance Payment'

        # form_vals = queryset.aggregate(
        # 	amount=Sum(F('maintenanceline__cost')) + (
        # 			Count('id', filter=Q(
        # 				flat__society__maintenance_due_days__lt=(datetime.now().date() - F('bill_date'))), distinct=True, output_field=FloatField()) *
        # 			Min(F('flat__society__maintenance_due_charge')))
        # )

        form_vals = queryset.aggregate(amount=Sum('total'))

        form_vals = dict(form_vals)

        context['form'] = forms.PaymentForm(initial=form_vals, request=request)
        request.session['maintenance_ids'] = list(queryset.values_list('pk', flat=True))
        return TemplateResponse(
            request,
            'admin/society/maintenance_payment.html',
            context,
        )

    actions = [make_payment]

    def get_urls(self):
        urls = super(MaintenanceAdmin, self).get_urls()
        custom_urls = [
            path(
                'maintenance_pdf/<int:object_id>/', self.admin_site.admin_view(reports.MaintenanceReport.as_view()),
                name='maintenance_pdf'),
        ]
        return custom_urls + urls

    def pay(self, request, object_id=None, *args, **kwargs):
        # do something
        pass


# def make_payment(self, obj):
# 	return format_html(
# 		'<a class="button" href="{}">Pay</a>',
# 		reverse('admin:pay', args=[obj.pk]),
# 	)


@admin.register(account.Transaction)
class TransactionAdmin(BaseAdmin):
    list_display = ['number', 'payment_method', 'amount']
    readonly_fields = ['uuid', 'amount', 'number']

    def get_urls(self):
        urls = super(TransactionAdmin, self).get_urls()
        custom_urls = [
            path('payment/', self.admin_site.admin_view(self.payment_view), name='payment_view', ),
        ]
        return custom_urls + urls

    def payment_view(self, request, object_id=None, *args, **kwargs):
        form = forms.PaymentForm(request.POST, request=request)
        print(form)
        print("form.is_valid()", form.is_valid())
        if form.is_valid():
            try:
                print("payment transaction>>>>", request.session['maintenance_ids'])
                form.save(user=request.user.id, maintenance_ids=request.session['maintenance_ids'],
                          society_id=request.session['society_ids'])
            except Exception as e:
                print(e)
            else:
                self.message_user(request, 'Payment Successful', messages.SUCCESS)
                if request.user.is_superuser:
                    url = reverse('admin:hsm_maintenance_changelist')
                else:
                    url = reverse('dashboard:maintenance_table')
                return HttpResponseRedirect(url)

        return True


# def save_model(self, request, obj, form, change):
# 	if obj._state.adding:
# 		obj.create_user = request.user
# 		print(obj.flat.society)
# 		society_id = obj.flat.society.pk
# 		service_lines = society.ServiceLine.objects.filter(society=society_id)
# 		for line in service_lines:
# 			obj.create
# 		import pdb; pdb.set_trace()
# 	obj.write_user = request.user
# 	super(BaseAdmin, self).save_model(request, obj, form, change)


@admin.register(account.PartnerAccount)
class Account(admin.ModelAdmin):
    list_display = ['name', 'balance']


# list_select_related = ['partner__name']


@admin.register(maintenance.FlatMaintenanceView)
class FlatMaintenanceViewAdmin(admin.ModelAdmin):
    change_list_template = 'admin/society/flat_maintenance.html'
    list_filter = [('state', AllValuesFieldListFilter)]
    date_hierarchy = 'bill_date'
    readonly_fields = ['bill_date', ]

    def get_urls(self):
        urls = super(FlatMaintenanceViewAdmin, self).get_urls()
        custom_urls = [
            path('<path:object_id>/maintenance/', self.admin_site.admin_view(self.view_maintenance),
                 name='flat-maintenance', ),
        ]
        return custom_urls + urls

    def view_maintenance(self, request, object_id, extra_context=None):
        # model = self.model
        #
        # print("sadfasdf", object_id)
        # # obj = self.get_object(request, unquote(object_id))
        # # if obj is None:
        # # 	return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)
        #
        # # Then get the history for this object.
        # opts = model._meta
        # app_label = opts.app_label
        #
        # context = {
        # 	**self.admin_site.each_context(request),
        # 	'title': _('Maintenance: %s') % obj,
        # 	'module_name': str(capfirst(opts.verbose_name_plural)),
        # 	# 'object': obj,
        # 	'opts': opts,
        # 	'preserved_filters': self.get_preserved_filters(request),
        # 	**(extra_context or {}),
        # }
        # request.current_app = self.admin_site.name
        return self.changelist_view(request, extra_context={'flat_id': object_id})

    # return TemplateResponse(request, 'admin/society/flat_maintenance.html', context)
    # return TemplateResponse(request, 'admin/society/flat_maintenance.html', context)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        print("qs", qs, extra_context)
        # metrics = {
        # 	'total': Count('id'),
        # 	'total_sales': Sum('price'),
        # }
        #
        # response.context_data['summary'] = list(
        # 	qs
        # 		.values('sale__category__name')
        # 		.annotate(**metrics)
        # 		.order_by('-total_sales')
        # )
        # print(qs.filter(maintenance__flat_id=extra_context['flat_id']).values('maintenance__name'))
        try:
            if extra_context and 'flat_id' in extra_context:
                qs = qs.filter(
                    flat=extra_context['flat_id']
                )
            qs = qs.annotate(
                flat_number=Concat('flat__wing__name', Value("-"), 'flat__number', output_field=CharField()),
                payment_method=F('transaction__payment_method'),
                bill_date_format=ExpressionWrapper(Func(F('bill_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                                   output_field=CharField()),
                paid_date_format=ExpressionWrapper(Func(F('paid_date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
                                                   output_field=CharField())
            ).values(
                'name',
                'flat_number',
                'bill_date_format',
                'paid_date_format',
                'state', 'payment_method'
            ).annotate(
                amount=Sum('total'),
                paid=Sum(F('total'), filter=Q(state=maintenance.Maintenance.STATE_TYPE_PAID)),
                unpaid=Sum(F('total'), filter=Q(state=maintenance.Maintenance.STATE_TYPE_UNPAID)),
                dues=Sum('total') - Sum('sub_total'),
            ).order_by(
                F('bill_date').desc(nulls_last=True)
            )
            qry, params = qs.query.sql_with_params()
            # print("params", qry, params)
            import re
            # qry = re.search(r'SELECT (.*), SUM', qry).group(0)
            # group_part = re.match(r'SELECT (.+?), SUM', qry).group(1)
            qry = re.sub(
                r'GROUP BY(.*) ORDER BY',
                r'GROUP BY GROUPING SETS((\1), ()) ORDER  BY', qry
            )
            # qry = qry.format(extra_context['flat_id'])
            from django.db import connections
            from psycopg2.extras import DictCursor, RealDictCursor, NamedTupleCursor

            conn = connections['default']
            conn.ensure_connection()

            with conn.connection.cursor(cursor_factory=DictCursor) as cr:
                cr.execute(qry, params)
                result = cr.fetchall()
            res_dict = []
            for rec in result:
                res_dict.append(dict(rec))
            # =======
            # 			# group_part = re.match(r'SELECT (.+?), SUM', qry).group(1)
            # 			# qry = re.sub(
            # 			# 	r'GROUP BY(.*) ORDER BY',
            # 			# 	r'GROUP BY GROUPING SETS((\1,'+group_part+'), ()) ORDER  BY', qry
            # 			# )
            #
            # 			# qry = qry.format(extra_context['flat_id'])
            # 			# from django.db import connection
            # 			# with connection.cursor() as cr:
            # 			# 	cr.execute(qry, params)
            # 			# 	result = cr.fetchall()
            # 			result = qs
            import json
            response.context_data['summary'] = json.dumps(res_dict)

            return response
        except Exception as e:
            import sys
            print("line number of error {}".format(sys.exc_info()[-1].tb_lineno))
            print("errorimage", e)


class ProductAdminInline(admin.TabularInline):
    model = PurchaseOrderLine
    fieldsets = [
        ('PurchaseOrderLine', {'fields': (
            ('product', 'quantity', 'unit_price'),
        )}),
    ]
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(BaseAdmin):
    list_display = ['order_date', 'number', 'download_purchase_order']
    search_fields = ['number']
    inlines = [ProductAdminInline]

    fieldsets = [
        ('Purchase Order Details', {'fields': (
            ('order_date', 'number'),
            ('society', 'vendor'),
            ('notes'),
        ), }),
    ]

    def download_purchase_order(self, obj):
        return format_html(
            '<a class="button" href="{}">Download</a>',
            reverse('admin:purchase_order_pdf', args=[obj.pk]),
        )

    def get_urls(self):
        urls = super(PurchaseOrderAdmin, self).get_urls()
        custom_urls = [
            path(
                'purchase_order_pdf/<path:object_id>/',
                self.admin_site.admin_view(reports.PurchaseOrderReport.as_view()),
                name='purchase_order_pdf'),
        ]
        return custom_urls + urls

    class Meta:
        proxy = True


@admin.register(helpdesk.Complaint)
class HelpDeskAdmin(BaseAdmin):
    list_display = ['create_date', 'number', 'download_complaint']
    search_fields = ['number']

    def download_complaint(self, obj):
        return format_html(
            '<a class="button" href="{}">Download</a>',
            reverse('admin:complaint_pdf', args=[obj.pk]),
        )

    def get_urls(self):
        urls = super(HelpDeskAdmin, self).get_urls()
        custom_urls = [
            path(
                'complaint_pdf/<path:object_id>/',
                self.admin_site.admin_view(reports.HelpDeskReport.as_view()),
                name='complaint_pdf'),
        ]
        return custom_urls + urls

    class Meta:
        proxy = True


admin.site.register(base.ResCountry, BaseAdmin)
admin.site.register(base.ResState, BaseAdmin)
admin.site.register(base.ResPost, BaseAdmin)
admin.site.register(base.ResPartnerType, BaseAdmin)
# admin.site.register(society.ResPartnerSociety, ResPartnerAdmin)


# admin.site.register(society.ResSociety, ResSocietyAdmin)
admin.site.register(society.ResWing, BaseAdmin)
# admin.site.register(society.ResFlat, ResFlatAdmin)

# admin.site.register(vehicle.VehicleBrand, BaseAdmin)
# admin.site.register(vehicle.VehicleModel, BaseAdmin)
admin.site.register(vehicle.VehicleParking, BaseAdmin)
admin.site.register(vehicle.PartnerVehicle, BaseAdmin)

admin.site.register(society.Service, BaseAdmin)
admin.site.register(society.Notice, BaseAdmin)
# admin.site.register(helpdesk.Complaint, BaseAdmin)
admin.site.register(helpdesk.ComplaintCategory, BaseAdmin)
# admin.site.register(society.ServiceLine, BaseAdmin)

admin.site.register(maintenance.MaintenanceLine, BaseAdmin)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(Vendor)
# admin.site.register(SocietyEmployeeDetail)
# admin.site.register(Job)
# admin.site.register(PurchaseOrderMaker)
