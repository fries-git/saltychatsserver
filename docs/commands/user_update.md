# Command: user_update

Update a user's profile information (owner only).

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

```json
{
  "cmd": "user_update",
  "user": "new_username",
  "nickname": "New Display Name"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "val": "User parameter is required"}`
- `{"cmd": "error", "val": "User not found"}`
- `{"cmd": "error", "val": "Updates must be an object"}`
- `{"cmd": "error", "val": "Cannot update field: <field>"}`
- `{"cmd": "error", "val": "Username must be a non-empty string"}`
- `{"cmd": "error", "val": "Nickname must be a string or null"}`

## Notes

- Requires `owner` role.
- Only `username` and `nickname` fields can be updated.
- Username changes take effect immediately across all systems.
- Setting `nickname` to `null` removes the nickname.
- Usernames are case-insensitive for lookup.

## See Also

- [user_delete](user_delete.md) - Delete a user
- [user_roles_add](user_roles_add.md) - Add roles to a user
- [user_roles_remove](user_roles_remove.md) - Remove roles from a user
- [users_list](users_list.md) - List all users

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "user_update":`).
