# Command: self_role_remove

Remove a self-assignable role from the authenticated user.

## Request

```json
{
  "cmd": "self_role_remove",
  "role": "role_name"
}
```

### Fields

- `role`: (required) The name of the self-assignable role to remove.

## Response

### On Success

```json
{
  "cmd": "self_role_remove",
  "role": "role_name",
  "success": true,
  "roles": ["user"]
}
```

### On Failure

If the role is not self-assignable:

```json
{
  "cmd": "error",
  "src": "self_role_remove",
  "val": "This role is not self-assignable"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "src": "self_role_remove", "val": "Role name is required"}`
- `{"cmd": "error", "src": "self_role_remove", "val": "Role not found"}`
- `{"cmd": "error", "src": "self_role_remove", "val": "This role is not self-assignable"}`
- `{"cmd": "error", "src": "self_role_remove", "val": "You don't have this role"}`
- `{"cmd": "error", "src": "self_role_remove", "val": "Failed to remove role"}`

## Notes

- Requires authentication.
- Only works with roles that have `self_assignable: true`.
- Protected roles (`owner`, `admin`, `moderator`) cannot be made self-assignable.
- Triggers a `self_role_remove` plugin event on success.

## Plugin Events

### `self_role_remove`

Triggered when a user successfully removes a self-assigned role.

Event data:
```json
{
  "user_id": "abc123",
  "username": "user@example.com",
  "role_name": "role_name"
}
```

## See Also

- [self_role_add](self_role_add.md) - Add a self-assignable role
- [self_roles_list](self_roles_list.md) - List available self-assignable roles
- [role_create](role_create.md) - Create a role (can set `self_assignable`)
- [role_update](role_update.md) - Update a role's `self_assignable` property

See implementation: [`handlers/messages/self_role.py`](../../handlers/messages/self_role.py)
