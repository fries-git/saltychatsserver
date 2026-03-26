# Command: role_update

Update an existing role's properties (owner only).

## Request

```json
{
  "cmd": "role_update",
  "name": "role_name",
  "description": "Updated description",
  "color": "#00FF00",
  "self_assignable": true
}
```

### Fields

- `name`: (required) The name of the role to update.
- `description`: (optional) New description for the role. If omitted, description is unchanged.
- `color`: (optional) New hex color code for the role. If omitted, color is unchanged.
- `self_assignable`: (optional) Boolean to enable/disable self-assignment. If omitted, setting is unchanged. Protected roles (`owner`, `admin`, `moderator`) cannot be made self-assignable.

## Response

### On Success

```json
{
  "cmd": "role_update",
  "name": "role_name",
  "updated": true
}
```

### On Failure

```json
{
  "cmd": "error",
  "src": "role_update",
  "val": "Role not found"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "val": "Role name is required"}`
- `{"cmd": "error", "val": "Role not found"}`
- `{"cmd": "error", "val": "Role 'owner' cannot be made self-assignable"}` (also for `admin`, `moderator`)

## Notes

- Requires `owner` role.
- Updates are applied to the role immediately.
- Changes to role color will be reflected for all users who have this role.
- Changes to role description are informational only.
- Cannot rename a role - use `role_delete` and `role_create` to rename.
- Setting `self_assignable: true` allows users to assign the role to themselves via `self_role_add`.

## See Also

- [role_create](role_create.md) - Create a new role
- [role_delete](role_delete.md) - Delete a role
- [role_list](role_list.md) - List all roles
- [self_role_add](self_role_add.md) - Self-assign a role
- [self_roles_list](self_roles_list.md) - List self-assignable roles

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "role_update":`).
