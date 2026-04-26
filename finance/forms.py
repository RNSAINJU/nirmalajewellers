
from django import forms
from decimal import Decimal, ROUND_HALF_UP
from .models import Loan, GoldLoanAccount

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['bank_name', 'amount', 'interest_rate', 'start_date', 'notes']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Loan Amount', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Interest Rate (%)', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control nepali-date', 'placeholder': 'Start Date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        }


class GoldLoanAccountForm(forms.ModelForm):
    class Meta:
        model = GoldLoanAccount
        fields = ['customer_name', 'phone_number', 'loan_amount', 'loan_taken_date', 'interest_rate', 'monthly_interest_amount', 'penalty_rate', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (optional)'}),
            'loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Loan Amount', 'step': '0.01'}),
            'loan_taken_date': forms.DateInput(attrs={'class': 'form-control nepali-date', 'placeholder': 'Loan Taken Date'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Interest Rate (%) (optional)', 'step': '0.01'}),
            'monthly_interest_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly Interest Amount (optional)', 'step': '0.01'}),
            'penalty_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Penalty Rate (%)', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        loan_amount = cleaned_data.get('loan_amount')
        interest_rate = cleaned_data.get('interest_rate')
        monthly_interest_amount = cleaned_data.get('monthly_interest_amount')

        if loan_amount in [None, ''] or Decimal(str(loan_amount)) <= Decimal('0'):
            raise forms.ValidationError('Loan Amount must be greater than 0.')

        loan_amount = Decimal(str(loan_amount))

        if interest_rate in [None, ''] and monthly_interest_amount in [None, '']:
            raise forms.ValidationError('Please enter either Interest Rate (%) or Monthly Interest Amount.')

        # Auto-calculate annual interest rate when monthly interest amount is given.
        if (interest_rate in [None, '']) and (monthly_interest_amount not in [None, '']):
            monthly_interest_amount = Decimal(str(monthly_interest_amount))
            calculated_rate = (monthly_interest_amount * Decimal('12') * Decimal('100')) / loan_amount
            cleaned_data['interest_rate'] = calculated_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Auto-calculate monthly interest amount when annual interest rate is given.
        if (monthly_interest_amount in [None, '']) and (interest_rate not in [None, '']):
            interest_rate = Decimal(str(interest_rate))
            calculated_monthly_interest = (loan_amount * interest_rate) / Decimal('100') / Decimal('12')
            cleaned_data['monthly_interest_amount'] = calculated_monthly_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return cleaned_data

from .models import Expense, Employee, EmployeeSalary, SundryDebtor, DebtorTransaction, SundryCreditor, CreditorTransaction, CashBank, CashBank


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'expense_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'base_salary', 'hire_date', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Base Salary', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmployeeSalaryForm(forms.ModelForm):
    class Meta:
        model = EmployeeSalary
        fields = ['employee', 'month', 'base_salary', 'bonus', 'deductions', 'amount_paid', 'status', 'paid_date', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Base Salary', 'step': '0.01'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bonus', 'step': '0.01'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Deductions', 'step': '0.01'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount Paid', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class SundryDebtorForm(forms.ModelForm):
    class Meta:
        model = SundryDebtor
        fields = ['name', 'contact_person', 'phone', 'address', 'bs_date', 'opening_balance', 'current_balance', 'credit_limit', 'is_paid', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Debtor Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Opening Balance', 'step': '0.01'}),
            'current_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current Balance', 'step': '0.01'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Credit Limit', 'step': '0.01'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class DebtorTransactionForm(forms.ModelForm):
    class Meta:
        model = DebtorTransaction
        fields = ['debtor', 'transaction_type', 'reference_no', 'amount', 'transaction_date', 'due_date', 'description']
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference No'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }


class SundryCreditorForm(forms.ModelForm):
    class Meta:
        model = SundryCreditor
        fields = ['name', 'contact_person', 'phone', 'address', 'bs_date', 'opening_balance', 'current_balance', 'is_paid', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Creditor Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Opening Balance', 'step': '0.01'}),
            'current_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current Balance', 'step': '0.01'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class CreditorTransactionForm(forms.ModelForm):
    class Meta:
        model = CreditorTransaction
        fields = ['creditor', 'transaction_type', 'reference_no', 'amount', 'transaction_date', 'due_date', 'description']
        widgets = {
            'creditor': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference No'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }


class CashBankForm(forms.ModelForm):
    class Meta:
        model = CashBank
        fields = ['account_type', 'account_name', 'bank_name', 'account_number', 'balance', 'notes', 'is_active']
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Main Cash, Petty Cash, NIC Asia Bank'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name (only for bank accounts)'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number (optional)'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current Balance', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].label = 'Active'
        
        # Filter out 'gold_loan' option - gold loans have dedicated module
        account_type_field = self.fields['account_type']
        account_type_field.choices = [
            (choice, label) for choice, label in account_type_field.choices 
            if choice != 'gold_loan'
        ]


class OtherInvestmentForm(forms.ModelForm):
    class Meta:
        model = CashBank
        fields = ['account_name', 'investment_date', 'investment_amount', 'current_amount', 'notes', 'is_active']
        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Share Market, FD, Mutual Fund'}),
            'investment_date': forms.TextInput(attrs={'class': 'form-control nepali-date', 'placeholder': 'Investment Date (BS)'}),
            'investment_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Original amount invested', 'step': '0.01'}),
            'current_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current market value', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].label = 'Active'
        self.fields['investment_date'].label = 'Investment Date (BS)'
        self.fields['investment_amount'].label = 'Investment Amount (रु)'
        self.fields['current_amount'].label = 'Current Value (रु)'

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.account_type = 'other_investment'
        # Set balance = current_amount for consistency with total assets calculation
        if instance.current_amount is not None:
            instance.balance = instance.current_amount
        elif instance.investment_amount is not None:
            instance.balance = instance.investment_amount
        if commit:
            instance.save()
        return instance
