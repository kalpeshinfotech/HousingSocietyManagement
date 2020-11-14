from ajax_select import LookupChannel, register

from . import models as base
from . import society


@register('society_look')
class PartnersPostLookup(LookupChannel):

	model = base.ResPartner

	def get_query(self, q, request):
		return self.model.objects.filter(name__icontains=q).order_by('name')


@register('partner_post_look')
class PartnersPostLookup(LookupChannel):

	model = base.ResPost

	def get_query(self, q, request):
		return self.model.objects.filter(name__icontains=q).order_by('name')
