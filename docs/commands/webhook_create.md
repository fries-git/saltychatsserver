# Command: webhook_create

Create a new webhook for a text channel. Requires `manage_server` permission.

## Request

```json
{
  "cmd": "webhook_create",
  "channel": "general",
  "name": "GitHub Notifications"
}
```

### Fields

- `channel`: (required) The name of the text channel to create the webhook for.
- `name`: (required) The name of the webhook.

## Response

### On Success

```json
{
  "cmd": "webhook_create",
  "webhook": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "channel": "general",
    "name": "GitHub Notifications",
    "token": "a1b2c3d4e5f6...",
    "created_by": "user_123",
    "created_at": 1703001234.567,
    "avatar": null
  }
}
```

The `token` field is only returned on creation. Store it securely as it won't be shown again.

## Error Responses

- `{"cmd": "error", "src": "webhook_create", "val": "Authentication required"}`
- `{"cmd": "error", "src": "webhook_create", "val": "Access denied: manage_server permission required"}`
- `{"cmd": "error", "src": "webhook_create", "val": "Channel is required"}`
- `{"cmd": "error", "src": "webhook_create", "val": "Webhook name is required"}`
- `{"cmd": "error", "src": "webhook_create", "val": "Channel not found"}`
- `{"cmd": "error", "src": "webhook_create", "val": "Webhooks can only be created for text channels"}`
- `{"cmd": "error", "src": "webhook_create", "val": "Failed to create webhook"}`

## Permissions

- Requires `manage_server` permission.

## Notes

- Webhooks can only be created by users with the `manage_server` permission.
- Webhooks can only be created for text channels.
- The returned token should be stored securely - it's used to authenticate HTTP POST requests.
- The webhook URL format is: `POST http://your-server/webhooks?token=<token>`

## Using Webhooks

Send a POST request to the webhook endpoint with a Discord-compatible JSON body:

```json
{
  "content": "Hello from webhook!",
  "username": "Custom Username",
  "avatar_url": "https://example.com/avatar.png"
}
```

### HTTP Request Format

```
POST /webhooks?token=<your_webhook_token> HTTP/1.1
Host: your-server.com
Content-Type: application/json
Content-Length: 52

{"content": "Hello from webhook!"}
```

### Discord Compatibility

The webhook endpoint accepts the same format as Discord webhooks:

- `content`: The message content (required if no embeds)
- `username`: Override the webhook's displayed username (optional)
- `avatar_url`: Override the webhook's displayed avatar URL (optional)
- `embeds`: Array of embed objects (optional)
- `text` / `message`: Alternative to `content` for compatibility

## See Also

- [webhook_list](webhook_list.md) - List webhooks
- [webhook_get](webhook_get.md) - Get a specific webhook
- [webhook_update](webhook_update.md) - Update a webhook
- [webhook_delete](webhook_delete.md) - Delete a webhook
- [webhook_regenerate](webhook_regenerate.md) - Regenerate webhook token

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "webhook_create":`).