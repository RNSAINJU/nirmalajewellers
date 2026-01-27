## Account Management - Code Examples

### Accessing Views Programmatically

#### Create a User
```python
from django.contrib.auth.models import User, Group

# Create a new user
user = User.objects.create_user(
    username='john_doe',
    email='john@example.com',
    password='secure_password_123',
    first_name='John',
    last_name='Doe'
)

# Add user to groups/roles
manager_group, created = Group.objects.get_or_create(name='Manager')
cashier_group, created = Group.objects.get_or_create(name='Cashier')

user.groups.add(manager_group, cashier_group)

# Make user staff
user.is_staff = True
user.save()
```

#### Query Users
```python
from django.contrib.auth.models import User, Group

# Get all active users
active_users = User.objects.filter(is_active=True)

# Get all staff users
staff_users = User.objects.filter(is_staff=True)

# Get all superusers
superusers = User.objects.filter(is_superuser=True)

# Get users with specific role
manager_role = Group.objects.get(name='Manager')
managers = manager_role.user_set.all()

# Get users by username
user = User.objects.get(username='john_doe')

# Get users by email
users_with_email = User.objects.filter(email='john@example.com')
```

#### Update User
```python
from django.contrib.auth.models import User

user = User.objects.get(username='john_doe')

# Update basic info
user.email = 'newemail@example.com'
user.first_name = 'Jane'
user.save()

# Change password
user.set_password('new_secure_password_123')
user.save()

# Disable user
user.is_active = False
user.save()

# Enable user
user.is_active = True
user.save()
```

#### Delete User
```python
from django.contrib.auth.models import User

user = User.objects.get(username='john_doe')
user.delete()
```

#### Create Roles/Groups
```python
from django.contrib.auth.models import Group

# Create new groups
manager_group, created = Group.objects.get_or_create(name='Manager')
cashier_group, created = Group.objects.get_or_create(name='Cashier')
sales_group, created = Group.objects.get_or_create(name='Sales Person')
accountant_group, created = Group.objects.get_or_create(name='Accountant')
viewer_group, created = Group.objects.get_or_create(name='Viewer')
```

#### Assign Roles to User
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='john_doe')
manager_group = Group.objects.get(name='Manager')

# Add user to group
user.groups.add(manager_group)

# Remove user from group
user.groups.remove(manager_group)

# Set all groups (replaces existing)
user.groups.set([manager_group, cashier_group])

# Clear all groups
user.groups.clear()

# Check if user has group
if user.groups.filter(name='Manager').exists():
    print("User is a manager")
```

### URLs for Forms and Views

```python
from django.urls import reverse

# Account Settings URLs
account_settings_url = reverse('main:account_settings')  
# /account-settings/

user_create_url = reverse('main:user_create')  
# /users/create/

user_update_url = reverse('main:user_update', args=[user_id])  
# /users/<user_id>/edit/

user_delete_url = reverse('main:user_delete', args=[user_id])  
# /users/<user_id>/delete/

user_password_url = reverse('main:user_change_password', args=[user_id])  
# /users/<user_id>/change-password/

role_list_url = reverse('main:role_list')  
# /roles/

role_create_url = reverse('main:role_create')  
# /roles/create/

role_update_url = reverse('main:role_update', args=[role_id])  
# /roles/<role_id>/edit/

role_delete_url = reverse('main:role_delete', args=[role_id])  
# /roles/<role_id>/delete/
```

### Using in Templates

```django
{# Link to account settings #}
<a href="{% url 'main:account_settings' %}">Account Settings</a>

{# Check if user is staff #}
{% if request.user.is_staff %}
    <p>User has staff access</p>
{% endif %}

{# Check if user is superuser #}
{% if request.user.is_superuser %}
    <p>User is superuser</p>
{% endif %}

{# Check if user has specific role #}
{% if request.user.groups.all|length > 0 %}
    <p>User has roles: {{ request.user.groups.all|join:", " }}</p>
{% endif %}

{# Check if user in specific group #}
{% if request.user.groups.filter|length %}
    <p>User is manager</p>
{% endif %}
```

### Custom Decorators for View Protection

```python
from django.contrib.auth.decorators import user_passes_test
from functools import wraps

# Check if user is staff
def staff_required(view_func):
    decorated_func = user_passes_test(lambda u: u.is_staff)(view_func)
    return decorated_func

# Check if user has specific role
def role_required(role_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name=role_name).exists():
                return view_func(request, *args, **kwargs)
            from django.shortcuts import redirect
            return redirect('login')
        return wrapper
    return decorator

# Usage:
@staff_required
def my_staff_view(request):
    return render(request, 'template.html')

@role_required('Manager')
def my_manager_view(request):
    return render(request, 'template.html')
```

### Custom Permissions Check in Views

```python
from django.http import HttpResponseForbidden

def my_view(request):
    # Check if user is staff
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Check if user has specific role
    if not request.user.groups.filter(name='Manager').exists():
        return HttpResponseForbidden("You must be a manager to access this page.")
    
    return render(request, 'template.html')
```

### Database Queries

```python
from django.contrib.auth.models import User, Group
from django.db.models import Q

# Get users who are staff OR superuser
users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))

# Get active users who are NOT staff
users = User.objects.filter(is_active=True, is_staff=False)

# Count users by group
from django.db.models import Count
group_stats = Group.objects.annotate(user_count=Count('user'))

# Get users with multiple groups
users_with_roles = User.objects.filter(groups__isnull=False).distinct()

# Get users created in last 30 days
from datetime import timedelta
from django.utils import timezone

thirty_days_ago = timezone.now() - timedelta(days=30)
new_users = User.objects.filter(date_joined__gte=thirty_days_ago)

# Search users
users = User.objects.filter(
    Q(username__icontains='john') |
    Q(email__icontains='john') |
    Q(first_name__icontains='john') |
    Q(last_name__icontains='john')
)
```

### Testing Account Features

```python
from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.test import Client

class AccountTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test group
        self.group = Group.objects.create(name='TestGroup')
        
        # Create client
        self.client = Client()
    
    def test_user_creation(self):
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='password123'
        )
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
    
    def test_user_login(self):
        login = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login)
    
    def test_role_assignment(self):
        self.user.groups.add(self.group)
        self.assertTrue(self.user.groups.filter(name='TestGroup').exists())
    
    def test_account_settings_access(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/account-settings/')
        # Non-staff user should get 403
        self.assertEqual(response.status_code, 403)
        
        # Make user staff and try again
        self.user.is_staff = True
        self.user.save()
        response = self.client.get('/account-settings/')
        self.assertEqual(response.status_code, 200)
```

### Signals for Account Changes (Optional)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created:
        print(f"New user created: {instance.username}")
        # Send email notification
        # Update audit log
        # etc.

# Disconnect signal if needed
post_save.disconnect(log_user_creation, sender=User)
```

### Common Issues & Solutions

**Problem:** Can't access account settings
```python
# Solution: Ensure user has is_staff=True
user = User.objects.get(username='john_doe')
user.is_staff = True
user.save()
```

**Problem:** User can't log in
```python
# Solution: Check if account is active
user = User.objects.get(username='john_doe')
if not user.is_active:
    user.is_active = True
    user.save()
```

**Problem:** Password not working
```python
# Solution: Reset password
from django.contrib.auth.models import User
user = User.objects.get(username='john_doe')
user.set_password('new_password_123')
user.save()
```

---

For more information, refer to [Django User Documentation](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/)
