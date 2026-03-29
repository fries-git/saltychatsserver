# Command: role_delete

Delete a role from the server (owner only).

## Request

```json
{
  "cmd": "role_delete",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Or by name:

```json
{
  "cmd": "role_delete",
  "name": "role_name"
}
```

### Fields

- `id`: (required or `name`) The ID of the role to delete.
- `name`: (optional, can be used instead of `id`) The name of the role to delete.

## Response

### On Success

```json
{
  "cmd": "role_delete",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "role_name",
  "deleted": true
}
```

### On Failure

```json
{
  "cmd": "error",
  "src": "role_delete",
  "val": "Role is used in channel 'general' permissions"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "val": "Role id or name is required"}`
- `{"cmd": "error", "val": "Role not found"}`
- `{"cmd": "error", "val": "Cannot delete system roles"}`
- `{"cmd": "error", "val": "Role is used in channel 'channel_name' permissions"}` - Role must be removed from all channel permissions first

## Notes

- Requires `owner` role.
- Cannot delete system roles: `owner`, `admin`, `user`.
- **The role is automatically removed from all users** that have it.
- The role must be removed from all channel permissions before deletion.
- Broadcasts `roles_list` to all connected clients after deletion.

## See Also

- [role_create](role_create.md) - Create a new role
- [role_update](role_update.md) - Update an existing role
- [roles_list](roles_list.md) - List all roles
- [channel_update](channel_update.md) - Update channel permissions

See implementation: [`handlers/messages/role.py`](../../handlers/messages/role.py).
