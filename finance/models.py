from decimal import Decimal
from datetime import date
from django.db import models
from django.utils import timezone
from nepali_datetime_field.models import NepaliDateField
from common.nepali_utils import bs_to_ad_date

class Loan(models.Model):
    """Model for loans from various banks"""
    bank_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate (%)")
    start_date = NepaliDateField()
    notes = models.TextField(blank=True, null=True)
    is_settled = models.BooleanField(default=False, help_text="Mark as settled/fully paid")
    settled_date = NepaliDateField(blank=True, null=True, help_text="Date when loan was settled")
    final_interest_paid = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Final interest paid at settlement")
    settlement_months = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Number of months the loan was active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']
        verbose_name_plural = "Loans"

    def __str__(self):
        return f"{self.bank_name} - रु{self.amount} @ {self.interest_rate}%"

    @property
    def monthly_interest(self):
        """Monthly interest amount"""
        return (self.amount * self.interest_rate) / Decimal('100') / Decimal('12')

    @property
    def quarterly_interest(self):
        """3-month tentative interest amount"""
        return self.monthly_interest * Decimal('3')

    @property
    def yearly_interest(self):
        """Yearly tentative interest amount"""
        return (self.amount * self.interest_rate) / Decimal('100')

    @property
    def total_interest_paid(self):
        """Total interest paid so far"""
        from django.db.models import Sum
        result = self.interest_payments.aggregate(Sum('amount'))['amount__sum']
        return result or Decimal('0')

    @property
    def total_months_covered(self):
        """Total months covered by all interest payments"""
        from django.db.models import Sum
        result = self.interest_payments.aggregate(Sum('months_covered'))['months_covered__sum']
        return result or Decimal('0')

    @property
    def implied_interest_rate(self):
        """Effective annual interest rate implied by actual payments made.
        Formula: (total_paid / loan_amount / total_months) * 12 * 100
        """
        total_months = self.total_months_covered
        if not total_months or self.amount == 0:
            return None
        rate = (self.total_interest_paid / self.amount / total_months) * Decimal('12') * Decimal('100')
        return round(rate, 2)

    @property
    def effective_interest_rate(self):
        """Calculate effective interest rate based on final interest paid and settlement months"""
        if not self.final_interest_paid or not self.settlement_months or self.amount == 0:
            return None
        
        # Formula: (Final Interest / Loan Amount) * (12 / Months) * 100
        # This converts the actual interest to an annualized percentage
        rate = (self.final_interest_paid / self.amount) * (Decimal('12') / Decimal(str(self.settlement_months))) * Decimal('100')
        return rate

    @property
    def final_interest_percentage(self):
        """Calculate final interest as percentage of loan amount"""
        if not self.final_interest_paid or self.amount == 0:
            return None
        
        # (Final Interest / Loan Amount) * 100
        percentage = (self.final_interest_paid / self.amount) * Decimal('100')
        return percentage


class LoanInterestPayment(models.Model):
    """Model for tracking 3-month interest payments on loans"""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='interest_payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = NepaliDateField()
    months_covered = models.DecimalField(max_digits=5, decimal_places=2, default=3, help_text="Number of months this payment covers (supports fractions e.g. 2.5)")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = "Loan Interest Payment"
        verbose_name_plural = "Loan Interest Payments"

    def __str__(self):
        return f"{self.loan.bank_name} - रु{self.amount} ({self.months_covered} months) on {self.payment_date}"


class GoldLoanAccount(models.Model):
    """Customer accounts for gold loans provided by the business."""

    customer_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    loan_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    loan_taken_date = NepaliDateField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Annual interest rate (%)")
    monthly_interest_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Direct monthly interest amount")
    penalty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('4.00'), help_text='Monthly penalty rate (%)')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-loan_taken_date', '-created_at']
        verbose_name = "Gold Loan Account"
        verbose_name_plural = "Gold Loan Accounts"

    def __str__(self):
        return f"{self.customer_name} - रु{self.loan_amount}"

    @property
    def effective_monthly_interest(self):
        if self.monthly_interest_amount is not None:
            return self.monthly_interest_amount
        if self.interest_rate is not None and self.loan_amount:
            return (self.loan_amount * self.interest_rate) / Decimal('100') / Decimal('12')
        return Decimal('0.00')

    @property
    def loan_taken_ad_date(self):
        """Best-effort AD date conversion for loan_taken_date."""
        value = self.loan_taken_date
        if not value:
            return None
        if hasattr(value, 'to_datetime_date'):
            try:
                return value.to_datetime_date()
            except Exception:
                pass
        try:
            return bs_to_ad_date(value)
        except Exception:
            return None

    @property
    def elapsed_days_to_date(self):
        start_date = self.loan_taken_ad_date
        if not start_date:
            return 0
        today = date.today()
        if start_date > today:
            return 0
        return (today - start_date).days

    @property
    def elapsed_months_to_date(self):
        # Approximate month span for running-interest display.
        return (Decimal(str(self.elapsed_days_to_date)) / Decimal('30')).quantize(Decimal('0.01'))

    @property
    def accrued_interest_to_date(self):
        """Accrued interest from loan date till current date."""
        monthly_interest = Decimal(str(self.effective_monthly_interest or Decimal('0.00')))
        if monthly_interest <= 0:
            return Decimal('0.00')
        accrued = monthly_interest * self.elapsed_months_to_date
        return accrued.quantize(Decimal('0.01'))


class GoldLoanInterestPayment(models.Model):
    """Tracks monthly interest payment confirmation rows for GoldLoanAccount."""

    account = models.ForeignKey(GoldLoanAccount, on_delete=models.CASCADE, related_name='interest_payments')
    period_label_bs = models.CharField(max_length=7, help_text='BS month label: YYYY-MM')
    period_start_ad = models.DateField()
    period_end_ad = models.DateField()
    interest_amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_on = NepaliDateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_start_ad', '-created_at']
        unique_together = ('account', 'period_start_ad', 'period_end_ad')
        verbose_name = 'Gold Loan Interest Payment'
        verbose_name_plural = 'Gold Loan Interest Payments'

    def __str__(self):
        return f"{self.account.customer_name} - {self.period_label_bs} - रु{self.interest_amount}"


class DhukutiLoan(models.Model):
    """Separate model for Dhukuti-style loans (kept distinct from standard loans)."""
    name = models.CharField(max_length=255)
    start_date = models.DateField(blank=True, null=True)
    received_amount = models.DecimalField(max_digits=14, decimal_places=2)
    total_kista = models.PositiveSmallIntegerField(default=20)
    received_kista_number = models.PositiveSmallIntegerField(
        default=1,
        help_text="Kista number in which whole amount was received."
    )
    remaining_base_payment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Dhukuti Loan"
        verbose_name_plural = "Dhukuti Loans"

    def __str__(self):
        return f"{self.name} - रु{self.received_amount}"

    @property
    def total_paid(self):
        from django.db.models import Sum
        result = self.paid_kistas.aggregate(Sum('amount'))['amount__sum']
        return result or Decimal('0')

    @property
    def paid_kista_count(self):
        return self.paid_kistas.count()

    @property
    def remaining_kista(self):
        remaining = self.total_kista - self.paid_kista_count
        return remaining if remaining > 0 else 0

    @property
    def total_interest(self):
        return self.received_amount - self.total_paid

    @property
    def average_interest_rate_percent(self):
        if not self.received_amount:
            return Decimal('0.00')
        return ((self.total_interest / self.received_amount) * Decimal('100')).quantize(Decimal('0.01'))


class DhukutiKistaPayment(models.Model):
    """Paid kista entries for a Dhukuti loan."""
    loan = models.ForeignKey(DhukutiLoan, on_delete=models.CASCADE, related_name='paid_kistas')
    month_number = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['month_number', 'created_at']
        unique_together = ['loan', 'month_number']
        verbose_name = "Dhukuti Kista Payment"
        verbose_name_plural = "Dhukuti Kista Payments"

    def __str__(self):
        return f"{self.loan.name} - Kista {self.month_number} - रु{self.amount}"


class DhukutiKistaPlan(models.Model):
    """Planned (not yet paid) kista entries for a Dhukuti loan."""
    loan = models.ForeignKey(DhukutiLoan, on_delete=models.CASCADE, related_name='planned_kistas')
    month_number = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['month_number', 'updated_at']
        unique_together = ['loan', 'month_number']
        verbose_name = "Dhukuti Kista Plan"
        verbose_name_plural = "Dhukuti Kista Plans"

    def __str__(self):
        return f"{self.loan.name} - Planned Kista {self.month_number} - रु{self.amount}"


class EmiLoan(models.Model):
    """Separate model for EMI loans (kept distinct from regular and Dhukuti loans)."""
    name = models.CharField(max_length=255)
    principal = models.DecimalField(max_digits=14, decimal_places=2)
    current_principal = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    annual_interest_rate = models.DecimalField(max_digits=7, decimal_places=4)
    tenure_months = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "EMI Loan"
        verbose_name_plural = "EMI Loans"

    def __str__(self):
        return f"{self.name} - रु{self.principal} @ {self.annual_interest_rate}%"


class Expense(models.Model):
    """Model for managing business expenses"""
    
    CATEGORY_CHOICES = [
        ('utilities', 'Utilities'),
        ('rent', 'Rent'),
        ('supplies', 'Supplies'),
        ('maintenance', 'Maintenance'),
        ('travel', 'Travel'),
        ('advertising', 'Advertising'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = NepaliDateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-expense_date']
        verbose_name_plural = "Expenses"
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.description} (रु{self.amount})"


class Employee(models.Model):
    """Model for employees"""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    position = models.CharField(max_length=100)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"


class EmployeeSalary(models.Model):
    """Model for managing employee salary payments"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    month = NepaliDateField()  # First day of the month
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_date = NepaliDateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        unique_together = ['employee', 'month']
    
    def __str__(self):
        return f"{self.employee.first_name} - {self.month.strftime('%B %Y')} (रु{self.total_salary})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total salary
        self.total_salary = self.base_salary + self.bonus - self.deductions
        super().save(*args, **kwargs)


class SundryDebtor(models.Model):
    """Model for managing sundry debtors (parties that owe money)"""
    
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bs_date = NepaliDateField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Sundry Debtors"
    
    def __str__(self):
        return f"{self.name} - Balance: रु{self.get_calculated_balance()}"
    
    def get_calculated_balance(self):
        """
        Calculate current balance based on transactions.
        Current Balance = Opening Balance + Invoices/Debit Memos - Payments/Credit Memos
        """
        from django.db.models import Sum
        
        # Get opening balance as starting point
        balance = self.opening_balance
        
        # Get all transactions and calculate balance
        transactions = self.transactions.all()
        
        if transactions.exists():
            # Add invoices and debit memos
            invoice_total = transactions.filter(
                transaction_type__in=['invoice', 'debit_memo']
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Subtract payments and credit memos
            payment_total = transactions.filter(
                transaction_type__in=['payment', 'credit_memo']
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            balance = balance + invoice_total - payment_total
        
        return balance
    
    def update_balance_from_transactions(self):
        """Update the current_balance field based on transaction calculations"""
        self.current_balance = self.get_calculated_balance()
        self.save(update_fields=['current_balance'])


class DebtorTransaction(models.Model):
    """Model for tracking individual transactions with debtors"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('payment', 'Payment'),
        ('credit_memo', 'Credit Memo'),
        ('debit_memo', 'Debit Memo'),
    ]
    
    debtor = models.ForeignKey(SundryDebtor, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.debtor.name} - {self.get_transaction_type_display()} - रु{self.amount}"
    
    def save(self, *args, **kwargs):
        """Auto-update debtor balance when transaction is saved"""
        super().save(*args, **kwargs)
        # Update the debtor's current_balance after transaction is saved
        self.debtor.update_balance_from_transactions()


class SundryCreditor(models.Model):
    """Model for managing sundry creditors (parties we owe money to)"""
    
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bs_date = NepaliDateField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Sundry Creditors"
    
    def __str__(self):
        return f"{self.name} - Balance: रु{self.get_calculated_balance()}"

    def get_calculated_balance(self):
        """
        Calculate current balance based on transactions.
        Current Balance = Opening Balance + Bills/Debit Memos - Payments/Credit Memos
        """
        from django.db.models import Sum

        balance = self.opening_balance

        transactions = self.transactions.all()

        if transactions.exists():
            bill_total = transactions.filter(
                transaction_type__in=['bill', 'debit_memo']
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')

            payment_total = transactions.filter(
                transaction_type__in=['payment', 'credit_memo']
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')

            balance = balance + bill_total - payment_total

        return balance

    def update_balance_from_transactions(self):
        """Update the current_balance field based on transaction calculations"""
        self.current_balance = self.get_calculated_balance()
        self.save(update_fields=['current_balance'])


class CreditorTransaction(models.Model):
    """Model for tracking individual transactions with creditors"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('bill', 'Bill'),
        ('payment', 'Payment'),
        ('credit_memo', 'Credit Memo'),
        ('debit_memo', 'Debit Memo'),
    ]
    
    creditor = models.ForeignKey(SundryCreditor, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.creditor.name} - {self.get_transaction_type_display()} - रु{self.amount}"

    def save(self, *args, **kwargs):
        """Auto-update creditor balance when transaction is saved"""
        super().save(*args, **kwargs)
        self.creditor.update_balance_from_transactions()


class CashBank(models.Model):
    """Model to track cash in hand and bank balances"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('cash', 'Cash in Hand'),
        ('bank', 'Bank Account'),
        ('gold_loan', 'Gold Loan'),
        ('other_investment', 'Other Investments'),
    ]
    
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='cash'
    )
    account_name = models.CharField(
        max_length=255,
        help_text='Name of the account (e.g., "Main Cash", "NIC Asia Bank")'
    )
    bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Bank name (only for bank accounts)'
    )
    account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Account number (only for bank accounts)'
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Current balance'
    )
    # Investment-specific fields (only used for account_type='other_investment')
    investment_date = NepaliDateField(
        blank=True, null=True,
        help_text='Date the investment was made'
    )
    investment_amount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True,
        help_text='Original amount invested'
    )
    current_amount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True,
        help_text='Current value of the investment'
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['account_type', 'account_name']
        verbose_name = "Cash/Bank Account"
        verbose_name_plural = "Cash/Bank Accounts"
    
    @property
    def profit_loss(self):
        """Calculate profit or loss for investments"""
        if self.investment_amount is not None and self.current_amount is not None:
            return self.current_amount - self.investment_amount
        return None
    
    def __str__(self):
        if self.account_type == 'bank':
            return f"{self.bank_name} - {self.account_name} (रु{self.balance})"
        return f"{self.account_name} (रु{self.balance})"
