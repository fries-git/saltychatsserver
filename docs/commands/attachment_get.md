# Command: attachment_get

Retrieve information about an attachment.

## Request

```json
{
  "cmd": "attachment_get",
  "attachment_id": "abc123-def456-ghi789"
}
```

### Fields

- `attachment_id`: (required) The unique identifier of the attachment.

## Response

### On Success

```json
{
  "cmd": "attachment_info",
  "attachment": {
    "id": "abc123-def456-ghi789",
    "name": "screenshot.png",
    "mime_type": "image/png",
    "size": 12345,
    "url": "https://your-server.com/attachments/abc123-def456-ghi789",
    "expires_at": 1712345678.9,
    "permanent": false
  }
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
- `{"cmd": "error", "val": "Invalid attachment_get command: ..."}`
- `{"cmd": "error", "val": "Attachment not found or expired"}`

## Notes

- Requires authentication.
- Returns `null` for `expires_at` if the attachment is permanent.
- Returns an error if the attachment has expired.

## See Also

- [attachment_upload](attachment_upload.md) - Upload an attachment
- [attachment_delete](attachment_delete.md) - Delete an attachment
