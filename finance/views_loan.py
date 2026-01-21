from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def loan_list(request):
    """Basic loan list page (placeholder)"""
    return render(request, 'finance/loan_list.html', {})
