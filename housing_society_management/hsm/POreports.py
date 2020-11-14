# from django.db.models import F, CharField, Value as V
# from django.db.models.functions import Concat
# from wkhtmltopdf.views import PDFTemplateView, PDFTemplateResponse
# from . import POMaker
# from django.shortcuts import redirect
# from django.db.models import (Case, CharField, Count, DateTimeField,
#                               ExpressionWrapper, F, FloatField, Func, Max, Min,
#                               Prefetch, Q, Sum, Value, When)
#
#
# class PurchaseOrderReport(PDFTemplateView):
#     filename = 'PurchaseOrder.pdf'
#     template_name = 'purchase_order/PurchaseOrder.html'
#     cmd_options = {
#         'margin-top': 3,
#     }
#
#     def get_data(self, request, purchase_order_id=None):
#         data = {}
#         purchase_order_lines = POMaker.PurchaseOrderLine.objects.annotate(product_name=F('product__name'))
#         record = POMaker.PurchaseOrderMaker.objects.filter(pk=purchase_order_id).annotate(
#             po_date=ExpressionWrapper(Func(F('date'), Value("DD/MM/YYYY"), function='TO_CHAR'),
#                                       output_field=CharField()),
#             society_name=F('society__name'),
#             society_address=Concat(
#                 F('society__partner__street1'), V(','), F('society__partner__street2'), V(','),
#                 F('society__partner__city'), V(','),
#                 F('society__partner__state__name'), V(','), F('society__partner__country__name'),
#                 V(','), F('society__partner__zip_code'),
#                 output_field=CharField()),
#             vendor_name=F('vendor__name'),
#             vendor_address=Concat(
#                 F('vendor__street1'), V(','), F('vendor__street2'), V(',\n '),
#                 F('vendor__city'), V(','), F('vendor__zip_code'), V(',\n '),
#                 F('vendor__state__name'), V(','), F('vendor__country__name'), V(',\n '),
#                 F('vendor__mobile_no'), V(',\n '), F('vendor__email'),
#                 output_field=CharField()),
#
#         ).prefetch_related(Prefetch('purchaseorderline_set', queryset=purchase_order_lines,
#                                     to_attr='purchase_order_lines'))
#
#         for each in record:
#             data.update({
#                 'society_name': each.society_name,
#                 'society_address': each.society_address,
#                 'vendor_name': each.vendor_name,
#                 'vendor_address': each.vendor_address,
#                 'purchase_order_no': each.purchase_order_no,
#                 'po_date': each.po_date,
#                 'grand_total': each.grand_total,
#                 'special_instructions': each.special_instructions,
#                 'pk': each.pk,
#                 'purchase_order_lines': [{'product_name': line.product_name,
#                                           'quantity': line.quantity,
#                                           'product_unit_price': line.product_unit_price} for line in
#                                          each.purchase_order_lines]
#             })
#         return data
#
#     def get(self, request, *args, **kwargs):
#         purchase_order_id = kwargs.get('object_id')
#         response = redirect(to='dashboard:dashboard')
#         context = self.get_data(request, purchase_order_id=purchase_order_id)
#
#         if context:
#             Purchase_order_file_name = POMaker.PurchaseOrderMaker.objects.filter(pk=purchase_order_id).annotate(
#                 Purchase_order_file_name=Concat(
#                     F('society__name'), V('_'),
#                     F('vendor__name'), V('-'),
#                     F('date'), V('.pdf'), output_field=CharField()),
#             ).values_list('Purchase_order_file_name', flat=True).first()
#             print("file_name", Purchase_order_file_name)
#             response = PDFTemplateResponse(request=request,
#                                            template=self.template_name,
#                                            filename=Purchase_order_file_name,
#                                            context=context,
#                                            show_content_in_browser=False,
#                                            cmd_options={'margin-top': 50, },
#                                            )
#             print("response", response)
#         return response
