from django.contrib.auth.models import User
# Create your models here.
from django.db import models
from django.utils import timezone
from django.utils.html import escape
from django_datatables_view.base_datatable_view import BaseDatatableView

from . import models as base
from .society import ResSociety


class ComplaintCategory(base.BaseModel):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'complaint_category'
        verbose_name_plural = 'Complaint Categories'
        verbose_name = 'Complaint Category'


class Complaint(base.BaseModel):
    from . import utils

    STATUS_SUBMITTED = 'Submitted'
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_COMPLETE = 'Completed'
    STATUS_CHOICES = (
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_COMPLETE, 'Completed'),
    )
    number = models.CharField(default=utils.encode, max_length=50, null=True)
    name = models.CharField(max_length=200)
    complaint_type = models.ForeignKey(ComplaintCategory, on_delete=models.SET_NULL, null=True, blank=False)
    comment = models.TextField(null=True)
    upload_file = models.FileField(upload_to='documents/', null=True, blank=True)
    status_type = models.CharField(choices=STATUS_CHOICES, max_length=20, null=True, blank=False)
    reply = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='complaint', null=True)
    society = models.ForeignKey(ResSociety, on_delete=models.PROTECT, related_name='complaint', null=True)

    class Meta:
        db_table = 'complaint'
        verbose_name_plural = 'Complaints'

    def __str__(self):
        return self.name


class MyComplaintDatatables(BaseDatatableView):
    model = Complaint
    columns = ['Date_time', 'Complaint_type', 'Comment', 'Status_type', 'Reply']
    order_columns = ['Date_time', 'Complaint_type', 'Comment', 'Status_type', 'Reply']

    def get_initial_queryset(self):
        return Complaint.objects.filter(create_user_id=self.request.user.id)
