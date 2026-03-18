# Command: webhook_regenerate

Regenerate a webhook's token (owner only).

## Request

```json
{
  "cmd": "webhook_regenerate",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Fields

- `id`: (required) The webhook ID to regenerate the token for.

## Response

### On Success

```json
{
  "cmd": "webhook_regenerate",
  "webhook": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "channel": "general",
    "name": "GitHub Notifications",
    "token": "new_token_value_here...",
    "created_by": "user_123",
    "created_at": 1703001234.567,
    "avatar": null
  }
}
```

The new `token` is returned. Store it securely - it won't be shown again.

## Error Responses

- `{"cmd": "error", "src": "webhook_regenerate", "val": "Authentication required"}`
- `{"cmd": "error", "src": "webhook_regenerate", "val": "Access denied: owner role required"}`
- `{"cmd": "error", "src": "webhook_regenerate", "val": "Webhook ID is required"}`
- `{"cmd": "error", "src": "webhook_regenerate", "val": "Webhook not found"}`
- `{"cmd": "error", "src": "webhook_regenate", "val": "Failed to regenerate webhook token"}`

## Notes

- Requires `owner` role.
- Regenerating the token invalidates the old token immediately.
- The new token is returned in the response - store it securely.
- External services using the old token will receive 401 errors after regeneration.
- Use this feature if you suspect the token has been compromised.

## Security Best Practices

1. Regenerate webhook tokens if they may have been exposed
2. Use HTTPS for webhook endpoints to protect tokens in transit
3. Store webhook tokens securely (not in client-side code)
4. Consider using environment variables for webhook tokens

## See Also

- [webhook_create](webhook_create.md) - Create a webhook
- [webhook_update](webhook_update.md) - Update webhook name/avatar
- [webhook_delete](webhook_delete.md) - Delete a webhook

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "webhook_regenerate":`).