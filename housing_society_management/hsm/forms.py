import uuid
import logging
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Sum
from django.forms import ModelForm
from django.utils import timezone

from . import account, maintenance
from .helpdesk import *


class PaymentForm(forms.ModelForm):
    # maintenance_ids = forms.MultipleChoiceField()

    class Meta:
        model = account.Transaction
        exclude = ['uuid', 'society', 'state']

        widgets = {
            'amount': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'cols': 58, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PaymentForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # import pdb;pdb.set_trace()
        # if instance and instance.pk:
        self.fields['amount'].widget.attrs['readonly'] = True

    def form_action(self, maintenance_ids, society_id, user):
        # vals = {
        # 	'user': user,
        # 	'amount': self.cleaned_data['amount'],
        # 	'asof': timezone.now(),
        # 	'payment_method': self.cleaned_data['payment_method'],
        # 	'number': self.cleaned_data['number'],
        # 	'reference': self.cleaned_data['reference'],
        # 	'notes': self.cleaned_data['notes'],
        # 	'maintenance_ids': maintenance_ids
        #
        # }
        vals = [
            user,
            timezone.now(),
            self.cleaned_data['amount'],
            self.cleaned_data['payment_method'],
            self.cleaned_data.get('number', ''),
            uuid.uuid4(),
            maintenance_ids,
            society_id,
            self.cleaned_data['reference'],
            self.cleaned_data['notes'],
        ]
        return account.Transaction.create(*vals)

    def save(self, *args, **kwargs):
        try:
            print("Payment form save")
            maintenance_ids, user, society_id = kwargs.get('maintenance_ids'), kwargs.get('user'), kwargs.get('society_ids')
            action = self.form_action(maintenance_ids, society_id, user)
            return action
        except Exception as e:
            error_message = str(e)
            self.add_error(None, error_message)
            raise

        # mail logic
        return super(PaymentForm, self).save(*args, **kwargs)

    def clean_amount(self):
        from .maintenance import Maintenance
        amount = Maintenance.objects.filter(
            id__in=self.request.session.get('maintenance_ids')
        ).aggregate(amount=Sum('total')).get('amount')
        logging.warning("amount %s maintenance_ids %s" % (amount, self.request.session.get('maintenance_ids')))
        return amount


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class HelpDeskForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['complaint_type', 'comment']
