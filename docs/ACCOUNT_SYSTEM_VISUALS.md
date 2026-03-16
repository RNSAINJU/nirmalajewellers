## Account Settings - Feature Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Account Management System                  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        v                   v                   v
   USER MANAGEMENT    ROLE MANAGEMENT    PERMISSIONS
        │                   │                   │
        ├─ Create           ├─ Create          ├─ Staff Status
        ├─ Edit             ├─ Edit            ├─ Superuser
        ├─ Delete           ├─ Delete          └─ Groups
        ├─ View List        └─ View List
        ├─ Search
        ├─ Filter
        ├─ Change Password
        └─ Pagination
```

### Access Flow

```
┌─────────────┐
│   Login     │
└──────┬──────┘
       │
       v
┌─────────────────────────┐
│   Is User Staff/Admin?  │
└──────┬──────┬───────────┘
       │      │
      Yes    No
       │      │
       │      v
       │  ┌───────────────────┐
       │  │   Access Denied   │
       │  │   (403 Forbidden) │
       │  └───────────────────┘
       │
       v
┌─────────────────────────────┐
│  Account Settings Dashboard │
└─────────────────────────────┘
       │
       ├─ View Users
       ├─ Manage Roles
       ├─ Create User
       ├─ Edit User
       ├─ Delete User
       └─ Change Password
```

### User Management Workflow

```
USER MANAGEMENT
│
├─ LIST USERS
│  │
│  ├─ Search (Username, Email, Name)
│  ├─ Filter by Status (Active/Inactive)
│  ├─ Filter by Role
│  └─ Pagination (20 per page)
│
├─ CREATE USER
│  │
│  ├─ Enter Username (required)
│  ├─ Enter Email (required)
│  ├─ Set Password (required)
│  ├─ First/Last Name (optional)
│  ├─ Assign Roles (optional, multiple)
│  ├─ Staff Status (toggle)
│  └─ Active Status (toggle)
│
├─ EDIT USER
│  │
│  ├─ Update Email
│  ├─ Update Name
│  ├─ Modify Roles
│  ├─ Toggle Staff Status
│  └─ Toggle Active Status
│
├─ CHANGE PASSWORD
│  │
│  ├─ Enter New Password
│  ├─ Confirm Password
│  └─ Update
│
└─ DELETE USER
   │
   ├─ Confirm Delete
   └─ Remove from System
```

### Role Management Workflow

```
ROLE MANAGEMENT
│
├─ LIST ROLES
│  │
│  ├─ Show All Roles
│  ├─ Display User Count per Role
│  └─ Quick Actions (Edit, Delete)
│
├─ CREATE ROLE
│  │
│  ├─ Enter Role Name
│  └─ Save
│
├─ EDIT ROLE
│  │
│  ├─ Update Role Name
│  └─ Save
│
└─ DELETE ROLE
   │
   ├─ Confirm Delete
   ├─ Show Affected Users
   └─ Remove Role
```

### Data Model

```
┌──────────────────────────┐
│      User Model          │
├──────────────────────────┤
│ • id (PK)               │
│ • username (Unique)     │
│ • email                 │
│ • first_name            │
│ • last_name             │
│ • password (Hashed)     │
│ • is_active             │
│ • is_staff              │
│ • is_superuser          │
│ • date_joined           │
│ • last_login            │
└──────────────────────────┘
         │
         │ (Many-to-Many)
         │
         v
┌──────────────────────────┐
│     Group Model          │
├──────────────────────────┤
│ • id (PK)               │
│ • name (Unique)         │
│ • permissions (M2M)     │
└──────────────────────────┘
```

### Feature Comparison Table

| Feature | User Management | Role Management |
|---------|-----------------|-----------------|
| Create | ✅ Create Users | ✅ Create Roles |
| Read | ✅ List/View Users | ✅ List/View Roles |
| Update | ✅ Edit User Details | ✅ Edit Role Names |
| Delete | ✅ Delete Users | ✅ Delete Roles |
| Search | ✅ Search Users | ❌ N/A |
| Filter | ✅ Filter by Status/Role | ❌ N/A |
| Multi-select | ✅ Assign Multiple Roles | ❌ N/A |
| Pagination | ✅ 20 per page | ❌ All at once |
| Bulk Actions | ❌ Individual Only | ❌ Individual Only |
| Export | ❌ Not Implemented | ❌ Not Implemented |

### Permission Matrix

```
┌─────────────┬──────────┬──────────┬────────────┐
│ Action      │ Regular  │ Staff    │ Superuser  │
├─────────────┼──────────┼──────────┼────────────┤
│ View Own    │ ✅ Yes   │ ✅ Yes   │ ✅ Yes     │
│ View Others │ ❌ No    │ ✅ Yes   │ ✅ Yes     │
│ Create User │ ❌ No    │ ✅ Yes   │ ✅ Yes     │
│ Edit User   │ ❌ No    │ ✅ Yes*  │ ✅ Yes     │
│ Delete User │ ❌ No    │ ✅ Yes*  │ ✅ Yes     │
│ Manage Roles│ ❌ No    │ ✅ Yes   │ ✅ Yes     │
│ Edit Superuser│ ❌ No  │ ❌ No    │ ✅ Yes     │
│ Delete Self │ ❌ No    │ ❌ No    │ ❌ No      │
└─────────────┴──────────┴──────────┴────────────┘
* Cannot edit/delete their own account or superuser accounts
```

### URL Structure

```
/account-settings/              Main Page
│
├─ Users
│  ├─ /users/create/            Create New User
│  ├─ /users/<id>/edit/         Edit User
│  ├─ /users/<id>/delete/       Delete User
│  └─ /users/<id>/change-password/  Change Password
│
└─ Roles
   ├─ /roles/                   List Roles
   ├─ /roles/create/            Create Role
   ├─ /roles/<id>/edit/         Edit Role
   └─ /roles/<id>/delete/       Delete Role
```

### Security Features Implemented

```
AUTHENTICATION
├─ Login Required (@login_required)
├─ Staff Check (@user_passes_test)
└─ Superuser Check (for sensitive operations)

AUTHORIZATION
├─ Staff/Superuser Only
├─ Superuser Protection (can't edit other superusers)
├─ Self-Protection (can't delete own account)
└─ Group-Based Access

FORM SECURITY
├─ CSRF Token Protection
├─ Input Validation
├─ Password Hashing
└─ Email Validation

DATABASE SECURITY
├─ ORM Queries (SQL Injection Prevention)
├─ Prepared Statements
└─ Model Validation
```

### Statistics Dashboard

```
┌─────────────────────────────────────────────┐
│       Account Settings Dashboard            │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Total Users  │  │ Active Users │        │
│  │     42       │  │      38      │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
│  ┌──────────────┐                          │
│  │ Staff Users  │                          │
│  │      8       │                          │
│  └──────────────┘                          │
│                                             │
└─────────────────────────────────────────────┘
```

### Filtering & Search Example

```
SEARCH & FILTER OPTIONS:
├─ Search Term: "john"
│  └─ Searches: username, email, first_name, last_name
│
├─ Status Filter: "Active"
│  └─ Shows only is_active=True users
│
├─ Role Filter: "Manager"
│  └─ Shows only users in Manager group
│
└─ Result: 5 users matching "john", active, in Manager role

PAGINATION:
├─ Page Size: 20 users
├─ Total: 127 users
├─ Pages: 7 (1-6 full, 7 with 7 users)
└─ Navigation: First, Previous, Page Numbers, Next, Last
```

### User Status Indicators

```
STATUS BADGES:

ACTIVE STATUS:
├─ 🟢 Active   - Can log in
└─ ⚪ Inactive - Cannot log in

USER TYPE:
├─ 🔵 Staff    - Has admin access
└─ ⚪ Regular  - Normal user access

SPECIAL:
├─ 🔴 Superuser - Full system access
└─ ⚫ Disabled   - Account deactivated
```

### Form Validation Flow

```
USER CREATE/EDIT FORM
│
├─ Username
│  ├─ Required
│  ├─ Unique
│  ├─ 150 chars max
│  └─ Alphanumeric + @.+-_
│
├─ Email
│  ├─ Required
│  ├─ Valid email format
│  └─ Can be non-unique
│
├─ Password
│  ├─ Required (create only)
│  ├─ 8 chars minimum
│  ├─ Cannot match username
│  └─ Common password check
│
├─ Name Fields
│  ├─ Optional
│  └─ 150 chars max
│
├─ Roles
│  ├─ Optional
│  └─ Multiple selection
│
├─ Flags
│  ├─ is_staff (toggle)
│  └─ is_active (toggle)
│
└─ Submit → Validation → Save/Error Message
```

### Common Use Cases

```
USE CASE 1: Onboard New Employee
├─ Create user account
├─ Assign "Sales Person" role
├─ Set is_staff = False
└─ Set is_active = True

USE CASE 2: Promote to Manager
├─ Edit user
├─ Add "Manager" role
├─ Set is_staff = True
└─ Save changes

USE CASE 3: Employee Leaves
├─ Edit user
├─ Set is_active = False (don't delete)
└─ Remove from roles

USE CASE 4: Create Role
├─ Go to Role Management
├─ Create "Regional Manager" role
├─ Assign users as needed
└─ Use for permission checks
```

---

This visual guide provides an overview of the entire account management system architecture and workflows.
