# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import redirect, render
#
# from .forms import HelpDeskForm, UserRegisterForm
# from .helpdesk import *
# from .society import Notice
#
# # Create your views here.
# # get wing data as per society
# # society.ResSociety.objects.filter(name='Lotus').values_list('society_wing_rel__name', flat=True)
#
# # get flat data as per society
# # society.ResSociety.objects.filter(name='Lotus').values_list(
# # 'resflat__number', 'resflat__wing__name', 'resflat__area', 'resflat__registration_number')
#
# def hsm_Home(request):
#     return render(request, 'hsm/Home.html')
#
#
# def hsm_register(request):
#     if request.method == 'POST':
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             messages.success(request, '{} your account is created you can login now !'.format(username))
#             return redirect('login')
#     else:
#         form = UserRegisterForm()
#     return render(request, 'hsm/register.html', {'form': form})
#
#
# @login_required
# def hsm_profile(request):
#     return render(request, 'hsm/profile.html')
#
#
# @login_required
# def hsm_notice(request):
#     notices = Notice.objects.order_by('-date')
#     context = {'notices': notices}
#     return render(request, 'hsm/notice.html', context)
#
#
# @login_required
# def hsm_helpdesk(request):
#     form = HelpDeskForm()
#     context = {'form': form}
#     if request.method == 'POST':
#         form = HelpDeskForm(request.POST)
#         if form.is_valid():
#             complaint = form.cleaned_data.get('complaint_type')
#             comment = form.cleaned_data.get('comment')
#             status = ComplaintDetail.STATUS_SUBMITTED
#             ComplaintDetail(
#                 name=request.user, complaint_type=complaint, comment=comment, status_type=status,
#                 create_user=request.user, write_user=request.user).save()
#             messages.success(request, '{} your complaint is generated !'.format(request.user))
#             return render(request, 'hsm/my_complaints.html')
#     return render(request, 'hsm/helpdesk.html', context)
#
#
# @login_required
# def hsm_my_complaints(request):
#     my_complaints = ComplaintDetail.objects.filter(Name=request.user)
#     context = {'complaints': my_complaints}
#     return render(request, 'hsm/my_complaints.html', context)
#
#
# @login_required
# def hsm_my_maintenance(request):
#     return render(request, 'hsm/my_maintenance.html')
#
#
# @login_required
# def hsm_Society_Mem_Details(request):
#     return render(request, 'hsm/Society.html')
