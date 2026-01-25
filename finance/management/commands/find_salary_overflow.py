from django.core.management.base import BaseCommand
from finance.models import EmployeeSalary

class Command(BaseCommand):
    help = 'Find EmployeeSalary records with extreme or invalid total_salary/amount_paid values.'

    def handle(self, *args, **options):
        errors = 0
        print('Checking EmployeeSalary records for overflow risk...')
        for salary in EmployeeSalary.objects.all():
            try:
                # Try to access and cast to float (simulate aggregation)
                float(salary.total_salary)
                float(salary.amount_paid)
            except Exception as e:
                errors += 1
                print(f'Error in record ID {salary.id}: {e} (total_salary={salary.total_salary}, amount_paid={salary.amount_paid})')
            # Check for abnormally large values
            if abs(salary.total_salary) > 1e8 or abs(salary.amount_paid) > 1e8:
                print(f'Extreme value in record ID {salary.id}: total_salary={salary.total_salary}, amount_paid={salary.amount_paid}')
        if errors == 0:
            print('No invalid records found.')
        else:
            print(f'Found {errors} invalid records.')
