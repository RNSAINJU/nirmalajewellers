from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models import Q
from .forms_accounts import UserCreateForm, UserUpdateForm, UserPasswordChangeForm, GroupForm


def is_staff_or_superuser(user):
    """Check if user is staff or superuser."""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_superuser)
def account_settings(request):
    """Main account settings page with user list."""
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    filter_role = request.GET.get('role', '')
    
    users = User.objects.all().prefetch_related('groups')
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if filter_status == 'active':
        users = users.filter(is_active=True)
    elif filter_status == 'inactive':
        users = users.filter(is_active=False)
    
    if filter_role:
        users = users.filter(groups__id=filter_role)
    
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all groups for filter dropdown
    all_groups = Group.objects.all().order_by('name')
    
    # Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_status': filter_status,
        'filter_role': filter_role,
        'all_groups': all_groups,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
    }
    return render(request, 'main/account_settings.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def user_create(request):
    """Create a new user."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" has been created successfully.')
            return redirect('main:account_settings')
    else:
        form = UserCreateForm()
    
    context = {
        'form': form,
        'title': 'Create New User',
        'button_text': 'Create User',
    }
    return render(request, 'main/user_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def user_update(request, user_id):
    """Update an existing user."""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent users from editing superusers unless they are superusers themselves
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit superuser accounts.')
        return redirect('main:account_settings')
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" has been updated successfully.')
            return redirect('main:account_settings')
    else:
        form = UserUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user,
        'title': f'Edit User: {user.username}',
        'button_text': 'Update User',
    }
    return render(request, 'main/user_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def user_delete(request, user_id):
    """Delete a user."""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent deletion of superusers unless by superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete superuser accounts.')
        return redirect('main:account_settings')
    
    # Prevent users from deleting themselves
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('main:account_settings')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted successfully.')
        return redirect('main:account_settings')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'main/user_confirm_delete.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def user_change_password(request, user_id):
    """Change password for a user."""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent changing password of superusers unless by superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to change password for superuser accounts.')
        return redirect('main:account_settings')
    
    if request.method == 'POST':
        form = UserPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for user "{user.username}" has been changed successfully.')
            return redirect('main:account_settings')
    else:
        form = UserPasswordChangeForm(user)
    
    context = {
        'form': form,
        'user_obj': user,
        'title': f'Change Password: {user.username}',
    }
    return render(request, 'main/user_password_change.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def role_list(request):
    """List all roles/groups."""
    groups = Group.objects.all().order_by('name')
    
    # Add user count to each group
    groups_with_counts = []
    for group in groups:
        groups_with_counts.append({
            'group': group,
            'user_count': group.user_set.count()
        })
    
    context = {
        'groups_with_counts': groups_with_counts,
    }
    return render(request, 'main/role_list.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def role_create(request):
    """Create a new role/group."""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Role "{group.name}" has been created successfully.')
            return redirect('main:role_list')
    else:
        form = GroupForm()
    
    context = {
        'form': form,
        'title': 'Create New Role',
        'button_text': 'Create Role',
    }
    return render(request, 'main/role_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def role_update(request, role_id):
    """Update an existing role/group."""
    group = get_object_or_404(Group, pk=role_id)
    
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{group.name}" has been updated successfully.')
            return redirect('main:role_list')
    else:
        form = GroupForm(instance=group)
    
    context = {
        'form': form,
        'group': group,
        'title': f'Edit Role: {group.name}',
        'button_text': 'Update Role',
    }
    return render(request, 'main/role_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def role_delete(request, role_id):
    """Delete a role/group."""
    group = get_object_or_404(Group, pk=role_id)
    
    if request.method == 'POST':
        group_name = group.name
        user_count = group.user_set.count()
        group.delete()
        messages.success(request, f'Role "{group_name}" has been deleted successfully. {user_count} users were affected.')
        return redirect('main:role_list')
    
    context = {
        'group': group,
        'user_count': group.user_set.count(),
    }
    return render(request, 'main/role_confirm_delete.html', context)
