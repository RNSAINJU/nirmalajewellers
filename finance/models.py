from decimal import Decimal
from django.db import models
from django.utils import timezone
from nepali_datetime_field.models import NepaliDateField


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
