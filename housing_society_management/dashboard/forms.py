from django import forms

from hsm import society
from hsm import helpdesk
from hsm import purchase
from ckeditor_uploader.widgets import CKEditorUploadingWidget


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = purchase.PurchaseOrder
        fields = ['number', 'order_date', 'vendor', 'notes']
        widgets = {
            'number': forms.HiddenInput(attrs={'class': 'form-control-sm'}),
            'order_date': forms.HiddenInput(attrs={'class': 'form-control-sm'}),
            'vendor': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'notes': forms.Textarea(attrs={'rows': 5, 'cols': 58, 'class': 'form-control-sm'}),
        }


class PurchaseLineForm(forms.ModelForm):
    class Meta:
        model = purchase.PurchaseOrderLine
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control form-control-sm', 'required': True}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control-sm', 'required': True}),
            'unit_price': forms.NumberInput(
                attrs={'class': 'form-control-sm', 'min': 0.0, 'step': 0.01, 'required': True}),
        }


data = {
    'form-TOTAL_FORMS': '1',
    'form-INITIAL_FORMS': '0',
    'form-MAX_NUM_FORMS': '',
}

PurchaseLineFormSet = forms.formset_factory(PurchaseLineForm)
PurchaseLineFormSetData = PurchaseLineFormSet(data)


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = helpdesk.Complaint
        exclude = ['status_type', 'reply', 'user', 'number', 'society']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'complaint_type': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'cols': 58, 'class': 'form-control'}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = society.Notice
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.CharField(widget=CKEditorUploadingWidget()),
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = helpdesk.Complaint
        fields = ['status_type', 'reply']
        widgets = {
            'status_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'reply': forms.Textarea(attrs={'rows': 5, 'cols': 58, 'class': 'form-control-sm'}),
        }
