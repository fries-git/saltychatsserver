# Command: attachment_upload

Upload a file attachment to the server. Attachments expire after a configurable time period, but users with certain Rotur subscription tiers can upload permanent attachments.

## Request

```json
{
  "cmd": "attachment_upload",
  "file": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "name": "screenshot.png",
  "mime_type": "image/png",
  "channel": "general"
}
```

### Fields

- `file`: (required) Base64-encoded file data, either as a data URI (`data:mime/type;base64,...`) or raw base64 string.
- `name`: (required) Original file name. Max 255 characters.
- `mime_type`: (required) MIME type of the file (e.g., `image/png`, `video/mp4`).
- `channel`: (required) Channel name where the attachment will be used.

## Response

### On Success

```json
{
  "cmd": "attachment_uploaded",
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

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Attachments are disabled"}`
- `{"cmd": "error", "val": "Channel does not exist"}`
- `{"cmd": "error", "val": "You don't have permission to send in this channel"}`
- `{"cmd": "error", "val": "Failed to save attachment"}`
- `{"cmd": "error", "val": "Invalid attachment_upload command: ..."}`

## Notes

- Requires authentication.
- File size is limited by `attachments.max_size` config (default: 100 MB).
- Only allowed MIME types can be uploaded (configurable via `attachments.allowed_types`).
- **Expiration is based on file size** - smaller files last longer:
  - ≤ 5 MB: 7 weeks (49 days)
  - 25 MB: 7 days
  - 100 MB: 1 day
- Users with Rotur Pro or Max subscriptions get permanent uploads (configurable via `attachments.permanent_tiers`).
- Permanent uploads expire after `attachments.permanent_expiration_days` days (default: 365 days).
- Uploads are rate-limited to `attachments.uploads_per_minute` per minute (default: 10).

## See Also

- [attachment_delete](attachment_delete.md) - Delete an attachment
- [attachment_get](attachment_get.md) - Get attachment info
- [message_new](message_new.md) - Send a message with attachments
