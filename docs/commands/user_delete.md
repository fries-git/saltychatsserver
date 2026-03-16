# Command: user_delete

Delete a user from the database (owner only).

## Request

```json
{
  "cmd": "user_delete",
  "user": "username_or_id"
}
```

### Fields

- `user`: (required) Username or user ID of the user to delete.

## Response

### On Success

```json
{
  "cmd": "user_delete",
  "user": "username",
  "deleted": true
}
```

Additionally, a `user_leave` broadcast is sent to all connected clients:

```json
{
  "cmd": "user_leave",
  "username": "username"
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "val": "User parameter is required"}`
- `{"cmd": "error", "val": "User not found"}`
- `{"cmd": "error", "val": "Cannot delete the last owner"}`

## Notes

- Requires `owner` role.
- Cannot delete the last user with `owner` role (at least one owner must remain).
- Deleting a user removes them from all databases immediately.
- All connected clients are notified via `user_leave` broadcast.
- This is permanent and cannot be undone.
- Usernames are case-insensitive for lookup.

## See Also

- [user_update](user_update.md) - Update user profile
- [user_ban](user_ban.md) - Ban a user
- [user_unban](user_unban.md) - Unban a user
- [users_list](users_list.md) - List all users
- [user_leave](user_leave.md) - User-initiated account deletion

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "user_delete":`).
