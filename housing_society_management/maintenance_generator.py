from hsm.maintenance import Maintenance, MaintenanceLine
from hsm.society import *
import random
from datetime import datetime


def maintenance_generator():
    for flat in ResFlat.objects.order_by('-society'):
        for soc in ResPartnerSociety.objects.all():
            if soc.name == flat.society.name:
                maintenance_name = f"MN-{random.randint(999, 10000)}"
                main_generator = Maintenance(name=maintenance_name, flat=flat, partner=soc,
                                             notes=f"This is maintenance note of yours of {datetime.now()}").save()


def maintenance_lines_generator():
    for maintenance in Maintenance.objects.all():
        for service in Service.objects.all():
            MaintenanceLine(maintenance=maintenance, service=service, cost=250).save()


maintenance_generator()
maintenance_lines_generator()

# ticket generator
# import random
# import string
#
#
# def randomString(stringLength=4):
#     """Generate a random string of fixed length """
#     letters = string.ascii_lowercase
#     return ''.join(random.choice(letters) for i in range(stringLength))
#
#
# for n in range(10):
#     print(f'{randomString()}-{random.randint(999, 10000)}')
