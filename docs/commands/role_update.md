# Command: role_update

Update an existing role's properties. Requires `manage_roles` permission.

## Request

```json
{
  "cmd": "role_update",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "new_role_name",
  "description": "Updated description",
  "color": "#00FF00",
  "self_assignable": true
}
```

### Fields

- `id`: (required or `name`) The ID of the role to update.
- `name`: (optional for lookup, can be used instead of `id`) The name of the role to update. Can also be used to rename the role when provided as an update field.
- `description`: (optional) New description for the role.
- `color`: (optional) New hex color code for the role. Pass `null` to clear.
- `hoisted`: (optional) Boolean to enable/disable separate display in user list.
- `self_assignable`: (optional) Boolean to enable/disable self-assignment. Protected roles (`owner`, `admin`, `moderator`) cannot be made self-assignable.
- `category`: (optional) Category name for grouping. Pass `null` to clear.
- `permissions`: (optional) Permissions object for the role.

## Response

### On Success

```json
{
  "cmd": "role_update",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "new_role_name",
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
- `{"cmd": "error", "val": "Access denied: manage_roles permission required"}`
- `{"cmd": "error", "val": "Role id or name is required"}`
- `{"cmd": "error", "val": "Role not found"}`
- `{"cmd": "error", "val": "Role 'owner' cannot be made self-assignable"}` (also for `admin`, `moderator`)

## Permissions

- Requires `manage_roles` permission.

## Notes

- Roles can only be updated by users with the `manage_roles` permission.
- Can use either `id` or `name` to identify the role.
- **Roles can now be renamed** by providing a new `name` field.
- Updates are applied to the role immediately.
- Changes to role color will be reflected for all users who have this role.
- Setting `self_assignable: true` allows users to assign the role to themselves via `self_role_add`.
- Broadcasts `roles_list` to all connected clients after update.

## See Also

- [role_create](role_create.md) - Create a new role
- [role_delete](role_delete.md) - Delete a role
- [roles_list](roles_list.md) - List all roles
- [self_role_add](self_role_add.md) - Self-assign a role

See implementation: [`handlers/messages/role.py`](../../handlers/messages/role.py).
