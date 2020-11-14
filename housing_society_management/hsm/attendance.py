# from .models import BaseModel
# from django.db import models
#
# class Job(BaseModel):
#     name = models.CharField(max_length=50, null=True, blank=False)
#     description = models.CharField(max_length=50, null=True, blank=True)
#
#     def __str__(self):
#         return self.name
#
#
# class SocietyEmployeeDetail(BaseModel):
#     society_name = models.CharField(max_length=50, null=True, blank=False)
#     emp_photo = models.ImageField(null=True, blank=False, upload_to=r'images')
#     emp_name = models.CharField(max_length=50, null=True, blank=False)
#     emp_address = models.TextField(max_length=100, null=True, blank=False)
#     emp_contact_no = models.CharField(max_length=10, null=True, blank=False)
#     emp_aadhar_card_no = models.CharField(max_length=12, null=True, blank=False)
#     emp_aadhar_card_photo = models.ImageField(null=True, blank=False, upload_to=r'images')
#     emp_pan_card_no = models.CharField(max_length=10, null=True, blank=False)
#     emp_pan_card_photo = models.ImageField(null=True, blank=False, upload_to=r'images')
#     emp_job_type = models.ForeignKey(Job, null=True, blank=False, on_delete=models.CASCADE)
#     emp_joining_date = models.DateTimeField(null=True, blank=False)
#     emp_working_hours = models.TimeField(null=True, blank=False)
#     emp_salary = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=False)
#
#     def __str__(self):
#         return self.emp_name
