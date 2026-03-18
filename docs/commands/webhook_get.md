# Command: webhook_get

Get information about a specific webhook (authenticated users).

## Request

```json
{
  "cmd": "webhook_get",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Fields

- `id`: (required) The webhook ID to get information for.

## Response

### On Success

```json
{
  "cmd": "webhook_get",
  "webhook": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "channel": "general",
    "name": "GitHub Notifications",
    "created_by": "user_123",
    "created_at": 1703001234.567,
    "avatar": null
  }
}
```

## Error Responses

- `{"cmd": "error", "src": "webhook_get", "val": "Authentication required"}`
- `{"cmd": "error", "src": "webhook_get", "val": "Webhook ID is required"}`
- `{"cmd": "error", "src": "webhook_get", "val": "Webhook not found"}`

## Notes

- Requires authentication.
- The `token` field is NOT included in the response for security.
- All authenticated users can get webhook information.

## See Also

- [webhook_create](webhook_create.md) - Create a webhook
- [webhook_list](webhook_list.md) - List webhooks
- [webhook_update](webhook_update.md) - Update a webhook
- [webhook_delete](webhook_delete.md) - Delete a webhook

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "webhook_get":`).