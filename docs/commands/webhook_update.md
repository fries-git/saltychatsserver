# Command: webhook_update

Update a webhook's name or avatar. Requires `manage_server` permission.

## Request

```json
{
  "cmd": "webhook_update",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "New Webhook Name",
  "avatar": "https://example.com/new-avatar.png"
}
```

### Fields

- `id`: (required) The webhook ID to update.
- `name`: (optional) New name for the webhook.
- `avatar`: (optional) New avatar URL for the webhook.

At least one of `name` or `avatar` must be provided.

## Response

### On Success

```json
{
  "cmd": "webhook_update",
  "webhook": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "channel": "general",
    "name": "New Webhook Name",
    "created_by": "user_123",
    "created_at": 1703001234.567,
    "avatar": "https://example.com/new-avatar.png"
  }
}
```

## Error Responses

- `{"cmd": "error", "src": "webhook_update", "val": "Authentication required"}`
- `{"cmd": "error", "src": "webhook_update", "val": "Access denied: manage_server permission required"}`
- `{"cmd": "error", "src": "webhook_update", "val": "Webhook ID is required"}`
- `{"cmd": "error", "src": "webhook_update", "val": "Webhook not found"}`
- `{"cmd": "error", "src": "webhook_update", "val": "Webhook name must be a non-empty string"}`
- `{"cmd": "error", "src": "webhook_update", "val": "No updates provided"}`
- `{"cmd": "error", "src": "webhook_update", "val": "Failed to update webhook"}`

## Permissions

- Requires `manage_server` permission.

## Notes

- Webhooks can only be updated by users with the `manage_server` permission.
- The `token` field is NOT included in the response for security.
- You cannot change the channel a webhook belongs to - create a new webhook instead.
- To change the token, use `webhook_regenerate`.

## See Also

- [webhook_create](webhook_create.md) - Create a webhook
- [webhook_list](webhook_list.md) - List webhooks
- [webhook_get](webhook_get.md) - Get a webhook
- [webhook_delete](webhook_delete.md) - Delete a webhook
- [webhook_regenerate](webhook_regenerate.md) - Regenerate webhook token

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "webhook_update":`).