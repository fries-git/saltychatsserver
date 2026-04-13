# Command: emoji_update

Update emoji metadata by ID. Requires `manage_server` permission.

## Request

```json
{
  "cmd": "emoji_update",
  "emoji_id": 0,
  "name": "defaultHuh",
  "image": "0.svg"
}
```

### Fields

- `emoji_id`: (required) Numeric emoji ID.
- `name`: (optional) New emoji name.
- `image`: (optional) New emoji image reference.

## Response

### On Success

```json
{
  "cmd": "emoji_update",
  "id": 0,
  "updated": true
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: manage_server permission required"}`
- `{"cmd": "error", "val": "At least one field to update is required (name or image)"}`
- `{"cmd": "error", "val": "Invalid emoji_update command scheme: ..."}` - When validation fails

## Permissions

- Requires `manage_server` permission.

## Notes

- Emojis can only be updated by users with the `manage_server` permission.
- At least one of `name` or `image` must be provided.
- The server maps `image` to the stored `fileName` metadata field.

## See Also

- [emoji_add](emoji_add.md) - Add a new emoji
- [emoji_get_all](emoji_get_all.md) - List all emojis

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "emoji_update":`).
