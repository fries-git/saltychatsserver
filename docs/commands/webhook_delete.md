# Command: webhook_delete

Delete a webhook (owner only).

## Request

```json
{
  "cmd": "webhook_delete",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Fields

- `id`: (required) The webhook ID to delete.

## Response

### On Success

```json
{
  "cmd": "webhook_delete",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted": true
}
```

## Error Responses

- `{"cmd": "error", "src": "webhook_delete", "val": "Authentication required"}`
- `{"cmd": "error", "src": "webhook_delete", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "src": "webhook_delete", "val": "Webhook ID is required"}`
- `{"cmd": "error", "src": "webhook_delete", "val": "Webhook not found"}`
- `{"cmd": "error", "src": "webhook_delete", "val": "Failed to delete webhook"}`

## Notes

- Requires `owner` role.
- Deletion is permanent - the webhook token will no longer work.
- Any external services using this webhook will receive 401 errors after deletion.

## See Also

- [webhook_create](webhook_create.md) - Create a webhook
- [webhook_list](webhook_list.md) - List webhooks
- [webhook_get](webhook_get.md) - Get a webhook
- [webhook_update](webhook_update.md) - Update a webhook

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "webhook_delete":`).