# Command: role_create

Create a new role. Requires `manage_roles` permission.

## Request

```json
{
  "cmd": "role_create",
  "name": "role_name",
  "description": "Optional role description",
  "color": "#FF0000",
  "self_assignable": true
}
```

### Fields

- `name`: (required) The name of the new role. Must be unique.
- `description`: (optional) A description of the role.
- `color`: (optional) Hex color code for the role (e.g., "#FF0000").
- `hoisted`: (optional) Boolean. If `true`, the role is displayed separately in the user list.
- `self_assignable`: (optional) Boolean. If `true`, users can assign this role to themselves. Protected roles (`owner`, `admin`, `moderator`) cannot be made self-assignable.
- `category`: (optional) Category name for grouping roles.
- `permissions`: (optional) Permissions object for the role.

## Response

### On Success

```json
{
  "cmd": "role_create",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "role_name"
}
```

### On Failure

If the role already exists:

```json
{
  "cmd": "error",
  "src": "role_create",
  "val": "Role already exists"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: manage_roles permission required"}`
- `{"cmd": "error", "val": "Role name is required"}`
- `{"cmd": "error", "val": "Role already exists"}`
- `{"cmd": "error", "val": "Role 'owner' cannot be made self-assignable"}` (also for `admin`, `moderator`)

## Permissions

- Requires `manage_roles` permission.

## Notes

- Roles can only be created by users with the `manage_roles` permission.
- Role names are case-sensitive.
- Role names cannot be the same as existing roles.
- The role is created with a unique `id` that can be used for lookups and renames.
- The role is created with no users assigned - use `user_roles_add` to assign it to users.
- The role can be used in channel permissions immediately after creation.
- Self-assignable roles can be assigned by users via `self_role_add` without owner intervention.

## See Also

- [role_update](role_update.md) - Update an existing role
- [role_delete](role_delete.md) - Delete a role
- [roles_list](roles_list.md) - List all roles
- [self_role_add](self_role_add.md) - Self-assign a role
- [self_roles_list](self_roles_list.md) - List self-assignable roles
- [user_roles_add](user_roles_add.md) - Add roles to a user

See implementation: [`handlers/messages/role.py`](../../handlers/messages/role.py).
