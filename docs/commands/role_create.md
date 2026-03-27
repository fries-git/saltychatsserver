# Command: role_create

Create a new role (owner only).

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
- `self_assignable`: (optional) Boolean. If `true`, users can assign this role to themselves. Protected roles (`owner`, `admin`, `moderator`) cannot be made self-assignable.

## Response

### On Success

```json
{
  "cmd": "role_create",
  "name": "role_name",
  "created": true
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
- `{"cmd": "error", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "val": "Role name is required"}`
- `{"cmd": "error", "val": "Role already exists"}`
- `{"cmd": "error", "val": "Role 'owner' cannot be made self-assignable"}` (also for `admin`, `moderator`)

## Notes

- Requires `owner` role.
- Role names are case-sensitive.
- Role names cannot be the same as existing roles.
- The role is created with no users assigned - use `user_roles_add` to assign it to users.
- The role can be used in channel permissions immediately after creation.
- Self-assignable roles can be assigned by users via `self_role_add` without owner intervention.

## See Also

- [role_update](role_update.md) - Update an existing role
- [role_delete](role_delete.md) - Delete a role
- [role_list](role_list.md) - List all roles
- [self_role_add](self_role_add.md) - Self-assign a role
- [self_roles_list](self_roles_list.md) - List self-assignable roles
- [user_roles_add](user_roles_add.md) - Add roles to a user

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "role_create":`).
