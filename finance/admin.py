from django.contrib import admin
from .models import Expense, Employee, EmployeeSalary, SundryDebtor, DebtorTransaction, SundryCreditor, CreditorTransaction, CashBank


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'description', 'amount', 'expense_date']
    list_filter = ['category', 'expense_date']
    search_fields = ['description', 'notes']
    date_hierarchy = 'expense_date'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'position', 'base_salary', 'is_active']
    list_filter = ['is_active', 'hire_date']
    search_fields = ['first_name', 'last_name', 'email', 'phone']


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'total_salary', 'amount_paid', 'status']
    list_filter = ['status', 'month']
    search_fields = ['employee__first_name', 'employee__last_name']
    date_hierarchy = 'month'


class DebtorTransactionInline(admin.TabularInline):
    model = DebtorTransaction
    extra = 1


@admin.register(SundryDebtor)
class SundryDebtorAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'opening_balance', 'current_balance', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    inlines = [DebtorTransactionInline]


@admin.register(DebtorTransaction)
class DebtorTransactionAdmin(admin.ModelAdmin):
    list_display = ['debtor', 'transaction_type', 'amount', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['debtor__name', 'reference_no']
    date_hierarchy = 'transaction_date'


class CreditorTransactionInline(admin.TabularInline):
    model = CreditorTransaction
    extra = 1


@admin.register(SundryCreditor)
class SundryCreditorAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'opening_balance', 'current_balance', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    inlines = [CreditorTransactionInline]


@admin.register(CreditorTransaction)
class CreditorTransactionAdmin(admin.ModelAdmin):
    list_display = ['creditor', 'transaction_type', 'amount', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['creditor__name', 'reference_no']


    @admin.register(CashBank)
    class CashBankAdmin(admin.ModelAdmin):
        list_display = ['account_name', 'account_type', 'bank_name', 'balance', 'is_active', 'updated_at']
        list_filter = ['account_type', 'is_active']
        search_fields = ['account_name', 'bank_name', 'account_number']
        readonly_fields = ['created_at', 'updated_at']
        fieldsets = [
            ('Account Information', {
                'fields': ('account_type', 'account_name', 'is_active')
            }),
            ('Bank Details', {
                'fields': ('bank_name', 'account_number'),
                'description': 'Only applicable for bank accounts'
            }),
            ('Balance', {
                'fields': ('balance',)
            }),
            ('Additional Information', {
                'fields': ('notes', 'created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        ]
    date_hierarchy = 'transaction_date'
