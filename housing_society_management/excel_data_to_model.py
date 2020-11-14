import pandas as pd
from hsm.society import *
from hsm.models import *
from hsm.maintenance import *

# Script for Society and ResPartner Details.
data = pd.read_excel(r'C:\Users\lenovo\Downloads\Society Full Details.xlsx', sheet_name='Sheet1')

society_col1 = pd.DataFrame(data, columns=['Name'])  # SocietyDetails
society_col2 = pd.DataFrame(data, columns=['RegistrationNo'])  # SocietyDetails
society_col3 = pd.DataFrame(data, columns=['Wings'])  # SocietyDetails
society_col4 = pd.DataFrame(data, columns=['Street1'])  # PartnerDetails
society_col5 = pd.DataFrame(data, columns=['Street2'])  # PartnerDetails
society_col6 = pd.DataFrame(data, columns=['City'])  # PartnerDetails
society_col7 = pd.DataFrame(data, columns=['Zipcode'])  # PartnerDetails
society_col8 = pd.DataFrame(data, columns=['MobileNo'])  # PartnerDetails
society_col9 = pd.DataFrame(data, columns=['AltMobileNo'])  # PartnerDetails
society_col10 = pd.DataFrame(data, columns=['Emailid'])  # PartnerDetails
society_col11 = pd.DataFrame(data, columns=['State'])
society_col12 = pd.DataFrame(data, columns=['Country'])

name = dict(society_col1.Name)  # SocietyDetails
rno = dict(society_col2.RegistrationNo)  # SocietyDetails
wings = dict(society_col3.Wings)  # SocietyDetails
st1 = dict(society_col4.Street1)  # PartnerDetails
st2 = dict(society_col5.Street2)  # PartnerDetails
city = dict(society_col6.City)  # PartnerDetails
zip_code = dict(society_col7.Zipcode)  # PartnerDetails
mobile_no = dict(society_col8.MobileNo)  # PartnerDetails
alt_mobile_no = dict(society_col9.AltMobileNo)  # PartnerDetails
email_id = dict(society_col10.Emailid)  # PartnerDetails
state = dict(society_col11.State)
country = dict(society_col12.Country)

# for SocietyDetails
for i in range(len(name)):
    Soc_details1 = ResSociety(name=name[i], registration_number=rno[i]).save()
    # for Respartner data.
    ResCountry.objects.get_or_create(name=country[i])
    country_name = ResCountry.objects.get(name=country[i])  # getting country for allocation in state and partner
    ResState.objects.get_or_create(name=state[i], country=country_name)
    state_name = ResState.objects.get(name=state[i])  # getting state for allocation in partner
    partner_details = ResPartner.objects.filter(name=name[i]).update(street1=st1[i], street2=st2[i], city=city[i],
                                                                     zip_code=zip_code[i], mobile_no=mobile_no[i],
                                                                     alt_mobile_no=alt_mobile_no[i], email=email_id[i],
                                                                     state=state_name, country=country_name)
    # for wings,state,country data.
    for j in wings[i].split(','):
        wing_name = ResWing.objects.get_or_create(name=j)

# Script for Society Flats
flat_data = pd.read_excel(r'C:\Users\lenovo\Downloads\Society Flat Details.xlsx', sheet_name='Sheet1')
flat_col1 = pd.DataFrame(flat_data, columns=['FlatNo'])
flat_col2 = pd.DataFrame(flat_data, columns=['WingName'])
flat_col3 = pd.DataFrame(flat_data, columns=['FlatArea_sqft'])
flat_col4 = pd.DataFrame(flat_data, columns=['RegistrationNumber'])
flat_col5 = pd.DataFrame(flat_data, columns=['RegistrationDate_yyyy_mm_dd'])
flat_col6 = pd.DataFrame(flat_data, columns=['Allocated_YES_or_NO'])
flat_col7 = pd.DataFrame(flat_data, columns=['Society'])
flat_col8 = pd.DataFrame(flat_data, columns=['FlatOwner'])
flat_col9 = pd.DataFrame(flat_data, columns=['FlatRenter'])

flat_no = dict(flat_col1.FlatNo)
flat_wing_names = dict(flat_col2.WingName)
flat_area = dict(flat_col3.FlatArea_sqft)
flat_registration_no = dict(flat_col4.RegistrationNumber)
flat_registration_date = dict(flat_col5.RegistrationDate_yyyy_mm_dd)
flat_allocated = dict(flat_col6.Allocated_YES_or_NO)
flat_society = dict(flat_col7.Society)
flat_owner = dict(flat_col8.FlatOwner)
flat_renter = dict(flat_col9.FlatRenter)

for i in range(len(flat_no)):
    society_name = ResSociety.objects.get(name=flat_society[i])
    flat_wing_name = ResWing.objects.get(name=flat_wing_names[i])
    Flat_detail = ResFlat(number=flat_no[i], area=flat_area[i], registration_number=flat_registration_no[i],
                          registration_date=flat_registration_date[i], society=society_name, wing=flat_wing_name).save()

# # Script for Maintainance
# Maintenance_data = pd.read_excel(r'C:\Users\lenovo\Downloads\MaintainanceDetails.xlsx', sheet_name='Sheet1')
# # print(Maintenance_data)
# Maintenance_col1 = pd.DataFrame(Maintenance_data, columns=['Name'])
# Maintenance_col2 = pd.DataFrame(Maintenance_data, columns=['Description'])
# Maintenance_col3 = pd.DataFrame(Maintenance_data, columns=['Society'])
# Maintenance_col4 = pd.DataFrame(Maintenance_data, columns=['Cost_Rs'])
#
# maintenance_name = dict(Maintenance_col1.Name)
# maintenance_description = dict(Maintenance_col2.Description)
# maintenance_society_name = dict(Maintenance_col3.Society)
# maintenance_cost = dict(Maintenance_col4.Cost_Rs)
#
# for i in range(len(maintenance_name)):
#     Maintenance_detail = Maintenance(name=maintenance_name[i], description=maintenance_description[i]).save()
#     maintenance_type = Maintenance.objects.get(name=maintenance_name[i])
#     maintenance_society_names = ResSociety.objects.get(name=maintenance_society_name[i])
#     MaintenanceLines(society=maintenance_society_names, maintenance_type=maintenance_type,
#                      cost=maintenance_cost[i]).save()
