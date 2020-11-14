from .society import ResSociety
from django.utils import timezone

from django.db import models
from .models import BaseModel, ResPartner, ResPartnerType
import random


def random_string():
    return str(random.randint(10000, 99999))


class ProductCategory(BaseModel):
    name = models.CharField(max_length=50, null=True, blank=False)
    description = models.TextField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'product_category'
        verbose_name_plural = 'Product Category'


class Product(BaseModel):
    from . import utils

    STOCKABLE = "Stockable"
    CONSUMABLE = "Consumable"
    SERVICE = "Services"
    TYPE_CHOICES = (
        (STOCKABLE, "Stockable"),
        (CONSUMABLE, "Consumable"),
        (SERVICE, "Services"),
    )
    number = models.CharField(default=utils.encode, max_length=50, null=True)
    name = models.CharField(max_length=50, null=True, blank=False)
    category = models.ForeignKey(ProductCategory, null=True, blank=False, on_delete=models.CASCADE)
    type = models.CharField(choices=TYPE_CHOICES, max_length=20, null=True, blank=False)
    description = models.TextField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'product'
        verbose_name_plural = 'Products'


class OnlyVendorManager(models.Manager):
    def get_queryset(self):
        return super(OnlyVendorManager, self).get_queryset().filter(partner_type__name='Vendor')


class Vendor(ResPartner):
    objects = OnlyVendorManager()

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None:
            partner_type_id = ResPartnerType.objects.get(name='Vendor')
            partner_obj = ResPartner.objects.create(name=self.name, partner_type=partner_type_id)
            self.partner = partner_obj
        res = super(Vendor, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
        return res

    class Meta:
        verbose_name_plural = 'Vendor Detail'
        proxy = True


class PurchaseOrder(BaseModel):
    from . import utils

    order_date = models.DateTimeField(default=timezone.now, null=True)
    number = models.CharField(default=utils.encode, max_length=50, null=True)
    society = models.ForeignKey(ResSociety, null=True, blank=False, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, null=True, blank=False, on_delete=models.CASCADE)
    notes = models.TextField(max_length=50, null=True, blank=True)
    grand_total = models.DecimalField(decimal_places=2, max_digits=10, default=0.00)

    def __str__(self):
        return str(self.number)

    class Meta:
        db_table = 'purchase_order'
        verbose_name_plural = 'Purchase Order'


class PurchaseOrderLine(BaseModel):
    purchase = models.ForeignKey(PurchaseOrder, null=True, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, null=True, blank=False)
    unit_price = models.FloatField(null=True, default=0.0)

    class Meta:
        db_table = 'purchase_order_line'
