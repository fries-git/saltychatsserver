# Endpoint: POST /attachments/upload

Upload a file attachment to the server via HTTP POST. Attachments expire after a configurable time period, but users with certain Rotur subscription tiers can upload permanent attachments.

## Authentication

This endpoint authenticates using the same credentials as WebSocket authentication. You need both:
- `validator_key`: Received in the `handshake` command during WebSocket connection
- `validator`: Your Rotur validator token used to authenticate via the WebSocket

These are included in the request body, not as headers.

## Request

- **Method**: POST
- **Content-Type**: application/json
- **Max Body Size**: Configurable via `attachments.max_size` (default: 100 MB)

### JSON Body

```json
{
  "validator_key": "originChats-xxxxxxxxxxxxxxxxxxxxxxxx",
  "validator": "your_rotur_validator_token",
  "file": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "name": "screenshot.png",
  "mime_type": "image/png",
  "channel": "general"
}
```

### Fields

- `validator_key`: (required) The validator key received in the WebSocket `handshake` command.
- `validator`: (required) Your Rotur validator token (same as used for WebSocket auth).
- `file`: (required) Base64-encoded file data, either as a data URI (`data:mime/type;base64,...`) or raw base64 string.
- `name`: (required) Original file name. Max 255 characters.
- `mime_type`: (required) MIME type of the file (e.g., `image/png`, `video/mp4`).
- `channel`: (required) Channel name where the attachment will be used.
- `expires_in_days`: (optional) Custom expiration in days. Max 365. Permanent uploads are limited by `permanent_expiration_days` config.

## Response

### On Success (201 Created)

```json
{
  "attachment": {
    "id": "abc123-def456-ghi789",
    "name": "screenshot.png",
    "mime_type": "image/png",
    "size": 12345,
    "url": "https://your-server.com/attachments/abc123-def456-ghi789",
    "expires_at": 1712345678.9,
    "permanent": false
  },
  "permanent": false
}
```

### Attachment Object Fields

- `id`: Unique attachment identifier (UUID).
- `name`: Original file name.
- `mime_type`: MIME type of the file.
- `size`: File size in bytes.
- `url`: URL to download the attachment.
- `expires_at`: Unix timestamp when the attachment expires (null for permanent).
- `permanent`: Whether the attachment is permanent.

## Error Responses

| Status | Error |
|--------|-------|
| 401 | `validator_key and validator are required for authentication` |
| 401 | `Invalid credentials` |
| 401 | `User ID not found in authentication response` |
| 401 | `User not found` |
| 415 | `Content-Type must be application/json` |
| 400 | `Invalid JSON body` |
| 400 | `Missing required fields: file, name, mime_type, channel` |
| 404 | `Channel does not exist` |
| 403 | `You don't have permission to send in this channel` |
| 413 | `Request body too large (max X bytes)` |
| 502 | `Failed to validate credentials` |
| 503 | `Attachments are disabled` |
| 500 | `Failed to save attachment` |

## Notes

- Requires valid `validator_key` and `validator` credentials from WebSocket connection.
- File size is limited by `attachments.max_size` config (default: 100 MB).
- Only allowed MIME types can be uploaded (configurable via `attachments.allowed_types`).
- **Expiration is based on file size** - smaller files last longer:
  - ≤ 5 MB: 7 weeks (49 days)
  - 25 MB: 7 days
  - 100 MB: 1 day
- Users with Rotur Pro or Max subscriptions get permanent uploads (configurable via `attachments.permanent_tiers`).
- Permanent uploads expire after `attachments.permanent_expiration_days` days (default: 365 days).

## Example

```bash
curl -X POST https://your-server.com/attachments/upload \
  -H "Content-Type: application/json" \
  -d '{
    "validator_key": "originChats-xxxxxxxxxxxxxxxxxxxxxxxx",
    "validator": "your_rotur_validator_token",
    "file": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "name": "screenshot.png",
    "mime_type": "image/png",
    "channel": "general"
  }'
```

## See Also

- [attachment_delete](attachment_delete.md) - Delete an attachment (WebSocket)
- [attachment_get](attachment_get.md) - Get attachment info (WebSocket)
- [message_new](message_new.md) - Send a message with attachments (WebSocket)
