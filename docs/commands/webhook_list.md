# Command: webhook_list

List all webhooks or webhooks for a specific channel (authenticated users).

## Request

### List All Webhooks

```json
{
  "cmd": "webhook_list"
}
```

### List Webhooks for a Channel

```json
{
  "cmd": "webhook_list",
  "channel": "general"
}
```

### Fields

- `channel`: (optional) Filter webhooks by channel name.

## Response

### On Success

```json
{
  "cmd": "webhook_list",
  "webhooks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "channel": "general",
      "name": "GitHub Notifications",
      "created_by": "user_123",
      "created_at": 1703001234.567,
      "avatar": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "channel": "general",
      "name": "CI/CD Alerts",
      "created_by": "user_456",
      "created_at": 1703002345.678,
      "avatar": "https://example.com/avatar.png"
    }
  ]
}
```

## Error Responses

- `{"cmd": "error", "src": "webhook_list", "val": "Authentication required"}`
- `{"cmd": "error", "src": "webhook_list", "val": "Channel not found"}`

## Notes

- Requires authentication.
- The `token` field is NOT included in the response for security.
- All authenticated users can list webhooks.
- Use `webhook_create` to create new webhooks (owner only).

## See Also

- [webhook_create](webhook_create.md) - Create a webhook
- [webhook_get](webhook_get.md) - Get a specific webhook
- [webhook_update](webhook_update.md) - Update a webhook
- [webhook_delete](webhook_delete.md) - Delete a webhook

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "webhook_list":`).