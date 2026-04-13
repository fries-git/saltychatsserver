# Command: user_roles_get

Get the roles assigned to a user. Requires `manage_users` permission.

## Request

```json
{
  "cmd": "user_roles_get",
  "user": "username_or_id"
}
```

### Fields

- `user`: (required) Username or user ID of the target user.

## Response

### On Success

```json
{
  "cmd": "user_roles_get",
  "user": "username",
  "roles": ["owner", "admin", "user"]
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: manage_users permission required"}`
- `{"cmd": "error", "val": "User parameter is required"}`
- `{"cmd": "error", "val": "User not found"}`

## Permissions

- Requires `manage_users` permission.

## Notes

- User roles can only be viewed by users with the `manage_users` permission.
- Usernames are case-insensitive for lookup.
- Roles are returned in priority order (highest priority first).
- The response includes the username as stored (with correct capitalization).
- The user's color is derived from their first (highest priority) role.
- This command is useful for verifying role assignments before managing them.

## See Also

- [user_roles_add](user_roles_add.md) - Add roles to a user
- [user_roles_remove](user_roles_remove.md) - Remove roles from a user
- [users_list](users_list.md) - List all users with their roles
- [role_list](role_list.md) - List all available roles

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "user_roles_get":`).
