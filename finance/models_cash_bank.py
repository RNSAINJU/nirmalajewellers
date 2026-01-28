from django.db import models
from decimal import Decimal

class CashBank(models.Model):
    """Model to track cash in hand and bank balances"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('cash', 'Cash in Hand'),
        ('bank', 'Bank Account'),
    ]
    
    account_type = models.CharField(
        max_length=10,
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
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['account_type', 'account_name']
        verbose_name = "Cash/Bank Account"
        verbose_name_plural = "Cash/Bank Accounts"
    
    def __str__(self):
        if self.account_type == 'bank':
            return f"{self.bank_name} - {self.account_name} (रु{self.balance})"
        return f"{self.account_name} (रु{self.balance})"
