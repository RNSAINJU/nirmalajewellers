## Account Settings - Quick Start

### Access Account Settings

1. **Log in** to the system with staff/admin account
2. Click **Settings** in the navigation sidebar
3. Select **Account Settings** from the dropdown

### Main Dashboard Overview

The Account Settings page displays:
- **📊 Statistics Cards**
  - Total Users
  - Active Users
  - Staff Users

- **🔍 Search & Filter Section**
  - Search by username, email, or name
  - Filter by status (Active/Inactive)
  - Filter by role/group

- **📋 User List Table**
  - Username with superuser badge if applicable
  - User full name
  - Email address
  - Assigned roles
  - Status (Active/Inactive)
  - User type (Staff/Regular)
  - Join date
  - Action buttons

### User Actions

**Add New User:**
```
1. Click "Add New User" button
2. Fill in username (required)
3. Enter email (required)
4. Enter first/last name (optional)
5. Set password
6. Assign roles (optional, multiple allowed)
7. Toggle "Staff Status" if admin access needed
8. Toggle "Active" to enable/disable account
9. Click "Create User"
```

**Edit User:**
```
1. Click pencil icon for user
2. Update fields as needed
3. Username is read-only
4. Modify roles, status, staff access
5. Click "Update User"
```

**Change Password:**
```
1. Click key icon for user
2. Enter new password twice
3. Click "Change Password"
```

**Delete User:**
```
1. Click trash icon for user
2. Review confirmation details
3. Click "Yes, Delete User" to confirm
```

### Role Management

**Access Role Management:**
```
1. From Account Settings, click "Manage Roles" button
2. Or navigate to Settings > Account Settings > Manage Roles
```

**Create Role:**
```
1. Click "Add New Role" button
2. Enter role name (e.g., "Manager", "Cashier")
3. Click "Create Role"
```

**Edit Role:**
```
1. Click pencil icon for role
2. Change role name
3. Click "Update Role"
```

**Delete Role:**
```
1. Click trash icon for role
2. Review how many users have this role
3. Click "Yes, Delete Role" to confirm
4. Users keep their accounts but lose this role
```

### Default Roles to Create

Consider creating these common roles:

1. **Manager**
   - Description: Full system access
   - Use case: Business owners, senior staff

2. **Cashier**
   - Description: Handle sales and payments
   - Use case: Front desk staff

3. **Sales Person**
   - Description: Create and manage orders
   - Use case: Sales representatives

4. **Accountant**
   - Description: Access financial reports
   - Use case: Finance team

5. **Viewer**
   - Description: Read-only access
   - Use case: Auditors, temporary staff

### User Statistics

The dashboard shows:
- **Total Users**: All users in system
- **Active Users**: Users with active status enabled
- **Staff Users**: Users with staff access

### Search Tips

- Search is **case-insensitive**
- Searches **username, email, first name, and last name**
- Results show **20 users per page**
- **Pagination** at bottom to navigate pages

### Filtering Tips

- **Status Filter**: Show only active or inactive users
- **Role Filter**: Show users with specific role
- **Combine Filters**: Use multiple filters together
- **Reset**: Clear search/filters by removing text

### User Status Badges

| Badge | Meaning |
|-------|---------|
| 🟢 Active | User can log in |
| ⚪ Inactive | User cannot log in |
| 🔵 Staff | User has admin access |
| ⚪ Regular | Regular user access |
| 🔴 Superuser | Full system access |

### Important Notes

⚠️ **Cannot Delete Self**: You cannot delete your own account

⚠️ **Superuser Protection**: Non-superusers cannot:
- Edit superuser accounts
- Delete superuser accounts
- Change superuser passwords

⚠️ **Active Status**: Inactive users cannot log in but are not deleted

✅ **Role Assignment**: Users can have multiple roles

✅ **Staff Status**: Makes user eligible for admin panel access

### Security Best Practices

1. **Assign Minimal Permissions**: Only give roles users need
2. **Review Regularly**: Periodically check active accounts
3. **Disable, Don't Delete**: Use inactive status for former employees
4. **Strong Passwords**: Enforce minimum password requirements
5. **Staff Access**: Limit staff status to trusted users

### Keyboard Shortcuts

- **Tab**: Navigate between form fields
- **Enter**: Submit forms
- **Escape**: Cancel/close dialogs

### Browser Support

Works best on:
- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (responsive design)

### Troubleshooting

**Can't see Account Settings:**
- Ensure you're logged in with staff/admin account
- Check if your account has `is_staff` status enabled

**Can't modify users:**
- Verify you have staff permissions
- Superusers can only be edited by other superusers

**Password change failed:**
- Ensure passwords match
- Password must be at least 8 characters
- Cannot be too similar to username

**Role not appearing:**
- Create the role first from Role Management
- Refresh page if recently created

---

For more detailed information, see [ACCOUNT_MANAGEMENT_GUIDE.md](ACCOUNT_MANAGEMENT_GUIDE.md)
