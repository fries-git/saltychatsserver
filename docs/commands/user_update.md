# Command: user_update

Update a user's profile information. Requires `manage_users` permission.

## Request

```json
{
  "cmd": "user_update",
  "user": "username_or_id",
  "updates": {
    "username": "new_username",
    "nickname": "New Display Name"
  }
}
```

### Fields

- `user`: (required) Username or user ID of the target user.
- `updates`: (required) Object containing fields to update.
  - `username`: (optional) New username for the user. Must be non-empty.
  - `nickname`: (optional) New display nickname. Pass `null` to remove.

## Response

### On Success

Broadcast to all connected clients:

```json
{
  "cmd": "user_updated",
  "user_id": "user-uuid",
  "username": "new_username",
  "nickname": "New Display Name"
}
```

Returns to the requester:

```json
{
  "cmd": "user_update",
  "user": "new_username",
  "nickname": "New Display Name"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: manage_users permission required"}`
- `{"cmd": "error", "val": "User parameter is required"}`
- `{"cmd": "error", "val": "User not found"}`
- `{"cmd": "error", "val": "Updates must be an object"}`
- `{"cmd": "error", "val": "Cannot update field: <field>"}`
- `{"cmd": "error", "val": "Username must be a non-empty string"}`
- `{"cmd": "error", "val": "Nickname must be a string or null"}`

## Permissions

- Requires `manage_users` permission.

## Notes

- User profiles can only be updated by users with the `manage_users` permission.
- Only `username` and `nickname` fields can be updated.
- Username changes take effect immediately across all systems.
- Setting `nickname` to `null` removes the nickname.
- Usernames are case-insensitive for lookup.
- Broadcasts `user_updated` (not full `users_list`) to all clients.

## See Also

- [user_delete](user_delete.md) - Delete a user
- [user_roles_set](user_roles_set.md) - Set user roles
- [users_list](users_list.md) - List all users

See implementation: [`handlers/messages/user.py`](../../handlers/messages/user.py).
