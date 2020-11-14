from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_datatables_view.base_datatable_view import BaseDatatableView


class BaseModel(models.Model):
	create_date = models.DateTimeField(default=timezone.now, null=True, blank=True, editable=False)
	write_date = models.DateTimeField(default=timezone.now, null=True, blank=True, editable=False)
	create_user = models.ForeignKey(
		User, related_name='created_by_%(app_label)s_%(class)s_related',
		on_delete=models.SET_NULL, null=True, editable=False)
	write_user = models.ForeignKey(
		User, related_name='written_by_%(app_label)s_%(class)s_related',
		on_delete=models.SET_NULL, null=True, editable=False)

	class Meta:
		abstract = True
	
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		return super(BaseModel, self).save(force_insert=False, force_update=False, using=None, update_fields=None)


class ResCountry(BaseModel):
	name = models.CharField(max_length=40, null=True, blank=False)
	code = models.CharField(max_length=40, null=True, blank=False)

	def __str__(self):
		return "["+str(self.code)+"] "+str(self.name)

	class Meta:
		db_table = 'res_countries'
		verbose_name_plural = 'Countries'


class ResState(BaseModel):
	name = models.CharField(max_length=40, null=True, blank=False)
	code = models.CharField(max_length=40, null=True, blank=False)
	country = models.ForeignKey(ResCountry, on_delete=models.SET_NULL, null=True, blank=False)

	def __str__(self):
		return self.name

	class Meta:
		db_table = 'res_states'
		verbose_name_plural = 'States'


class ResPartnerType(BaseModel):
	name = models.CharField(max_length=40, null=True, blank=False)

	class Meta:
		db_table = 'res_partner_type'

	def __str__(self):
		return self.name


class ResPost(BaseModel):
	name = models.CharField(max_length=40, null=True, blank=False)
	period = models.IntegerField(null=True, blank=True)
	period_type = models.CharField(max_length=10, null=True, blank=True)

	def __str__(self):
		return self.name

	class Meta:
		db_table = 'res_posts'


class ResPartner(BaseModel):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=40, null=True, blank=False)
	street1 = models.CharField(max_length=40, null=True, blank=False)
	street2 = models.CharField(max_length=40, null=True, blank=True)
	city = models.CharField(max_length=40, null=True, blank=False)
	state = models.ForeignKey(ResState, on_delete=models.SET_NULL, null=True, blank=False)
	country = models.ForeignKey(ResCountry, on_delete=models.SET_NULL, null=True, blank=False)
	zip_code = models.IntegerField(null=True, blank=False)
	mobile_no = models.CharField(max_length=15, null=True)
	alt_mobile_no = models.CharField(max_length=15, null=True, blank=True)
	email = models.CharField(max_length=40, null=True, blank=True)
	is_active = models.BooleanField(default=True, null=False, blank=True)

	user = models.ForeignKey(User, related_name='partner_user', on_delete=models.SET_NULL, null=True, blank=True)
	partner_type = models.ForeignKey(ResPartnerType, on_delete=models.SET_NULL, null=True, blank=True)
	partner_post_rel = models.ManyToManyField(
		ResPost, db_table='partner_post_rel', blank=True, verbose_name='Partner post(s)')
	society = models.ManyToManyField(
		'hsm.ResSociety', db_table='partner_society_rel', blank=True, verbose_name='Society(s)')
	dob = models.DateField(null=True, verbose_name='Date of Birth')
	# from hsm.account import PartnerAccount
	account = models.ForeignKey('hsm.PartnerAccount', on_delete=models.PROTECT, null=True, blank=True)

	class Meta:
		db_table = 'res_partners'
		verbose_name_plural = 'Members'
		verbose_name = 'Member'

	def __str__(self):
		return self.name

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		from . import account
		from .utils import encode
		post_str = encode()
		if self.pk is None:
			res = super(ResPartner, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
			user_obj = User.objects.create_user(
				username='USR_'+post_str, password=None, is_staff=True, email=self.email,
				first_name=self.name
			)
			self.user = user_obj
			if not self.partner_type:
				partner_type_id = ResPartnerType.objects.get(name='Individual')
				self.partner_type = partner_type_id
			self.account = account.PartnerAccount.objects.create(name='AC-'+post_str)
			self.save()
		else:
			res = super(ResPartner, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
		return res


class MembersDatatables(BaseDatatableView):
	model = ResPartner
	columns = ['name', 'street1', 'street2', 'city', 'state', 'country', 'zip_code ', 'mobile_no',
			   'alt_mobile_no', 'email']
	order_columns = ['name', 'street1', 'street2', 'city', 'state', 'country', 'zip_code ', 'mobile_no',
					 'alt_mobile_no', 'email']
