import time

from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from . import account
from . import models as base


class ResWing(base.BaseModel):
    name = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'res_wings'
        ordering = ['pk', 'name']
        verbose_name_plural = 'Wings'
        verbose_name = 'Wing'


class ResSociety(base.BaseModel):
    name = models.CharField(max_length=40, null=True, blank=False)
    registration_number = models.CharField(max_length=40, unique=True, null=True, blank=False)
    partner = models.ForeignKey('hsm.ResPartner', related_name='society_user', on_delete=models.SET_NULL, null=True,
                                blank=True)
    society_wing_rel = models.ManyToManyField(ResWing, db_table='society_wing_rel')
    is_active = models.BooleanField(default=True, null=True, blank=True)
    maintenance_due_days = models.PositiveIntegerField(default=0)
    maintenance_due_charge = models.FloatField(default=0)

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None:
            partner_type_id = base.ResPartnerType.objects.get(name='Society')
            partner_obj = base.ResPartner.objects.create(name=self.name, partner_type=partner_type_id)
            self.partner = partner_obj
        res = super(ResSociety, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
        return res

    class Meta:
        db_table = 'res_societies'
        verbose_name_plural = 'Societies'


# class ResPartnerSociety(base.ResPartner):
# society = models.ManyToManyField(
# 	ResSociety, db_table='partner_society_rel', blank=True, verbose_name='Society(s)')


class ResFlat(base.BaseModel):
    number = models.IntegerField(null=True, blank=False)
    wing = models.ForeignKey(ResWing, on_delete=models.SET_NULL, null=True, blank=False)
    area = models.IntegerField(null=True, blank=False)
    registration_number = models.CharField(max_length=40, unique=True, null=True, blank=False)
    registration_date = models.DateTimeField(max_length=40, null=True, blank=False)
    is_allocated = models.BooleanField(default=0, null=True, blank=True)
    society = models.ForeignKey(ResSociety, on_delete=models.SET_NULL, null=True, blank=False)
    is_active = models.BooleanField(default=True, null=True, blank=True)

    flat_owner = models.ManyToManyField(
        base.ResPartner, related_name='owner_flat', db_table='owner_flat_rel', blank=True, verbose_name='Owner(s)')
    flat_renter = models.ManyToManyField(
        base.ResPartner, related_name='renter_flat', db_table='renter_flat_rel', blank=True, verbose_name='Renter(s)')

    def __str__(self):
        # return ''.join([str(self.wing.name), '-', str(self.number)])
        return str(self.number)

    class Meta:
        db_table = 'res_flats'
        verbose_name = 'Flat'
        verbose_name_plural = 'Flats'
        ordering = ['number', 'wing', 'society']


class Service(base.BaseModel):
    name = models.CharField(max_length=40, null=True, blank=False)
    account = models.ForeignKey('hsm.PartnerAccount', on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)

    class Meta:
        db_table = 'services'

    def __str__(self):
        return str(self.name)


class SocietyServiceLine(base.BaseModel):
    service_type = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=False)
    account = models.ForeignKey('hsm.PartnerAccount', null=True, on_delete=models.PROTECT, blank=True)
    price = models.IntegerField(null=True, blank=False)
    society = models.ForeignKey(ResSociety, on_delete=models.PROTECT, blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        from . import account
        from .utils import encode
        if self.pk is None:
            res = super(SocietyServiceLine, self).save(force_insert=False, force_update=False, using=None,
                                                       update_fields=None)
            self.account = account.PartnerAccount.objects.create(name='SVC-' + encode())
            self.save()
        else:
            res = super(SocietyServiceLine, self).save(force_insert=False, force_update=False, using=None,
                                                       update_fields=None)
        return res

    class Meta:
        db_table = 'society_service_lines'

    def __str__(self):
        return str(''.join([self.service_type.name, '[', self.account.name, ']']))


@api_view(['GET', 'POST'])
@permission_classes((AllowAny,))
def get_wings_by_society(request):
    society_id = request.POST.get('society_id')
    wings = []
    if society_id:
        wings = list(ResWing.objects.filter(ressociety=society_id).values('pk', 'name'))
    return JsonResponse(wings, safe=False, status=200)


class Notice(base.BaseModel):
    title = models.CharField(max_length=20, null=True, blank=False)
    date = models.DateTimeField(default=timezone.now, null=True, blank=False)
    description = RichTextUploadingField(null=True, blank=False)
    society = models.ForeignKey(ResSociety, on_delete=models.SET_NULL, null=True, blank=False)

    def __str__(self):
        return str(self.title)
