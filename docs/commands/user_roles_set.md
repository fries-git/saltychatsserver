# Command: user_roles_set

Set the exact roles for a user. Requires `manage_users` permission.

## Request

```json
{
  "cmd": "user_roles_set",
  "user": "username_or_id",
  "roles": ["admin", "moderator"]
}
```

### Fields

- `user`: (required) Username or user ID of the target user.
- `roles`: (required) Array of role names to set as the user's roles (replaces all existing roles).

## Response

### On Success

```json
{
  "cmd": "user_roles_set",
  "user": "username",
  "roles": ["admin", "moderator"],
  "set": true
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: manage_users permission required"}`
- `{"cmd": "error", "val": "User parameter is required"}`
- `{"cmd": "error", "val": "Roles list is required"}`
- `{"cmd": "error", "val": "User not found"}`
- `{"cmd": "error", "val": "Role 'role_name' does not exist"}`
- `{"cmd": "error", "val": "Cannot remove all roles from a user"}`

## Permissions

- Requires `manage_users` permission.

## Notes

- User roles can only be set by users with the `manage_users` permission.
- Completely replaces the user's existing roles with the provided list.
- At least one role must be provided.
- All roles must exist before being assigned to a user.
- Usernames are case-insensitive for lookup but are stored as provided during registration.
- Role changes take effect immediately for all future actions by the user.
- The user's role color will update to match their highest-priority role (first in list).

## See Also

- [user_roles_get](user_roles_get.md) - Get a user's roles
- [role_create](role_create.md) - Create a new role
- [user_ban](user_ban.md) - Ban a user

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "user_roles_set":`).
