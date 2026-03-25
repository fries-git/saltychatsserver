# Command: attachment_delete

Delete an attachment you uploaded. Only the uploader or users with owner/admin roles can delete attachments.

## Request

```json
{
  "cmd": "attachment_delete",
  "attachment_id": "abc123-def456-ghi789"
}
```

### Fields

- `attachment_id`: (required) The unique identifier of the attachment to delete.

## Response

### On Success

```json
{
  "cmd": "attachment_deleted",
  "attachment_id": "abc123-def456-ghi789",
  "deleted": true
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Invalid attachment_delete command: ..."}`
- `{"cmd": "error", "val": "Attachment not found"}`
- `{"cmd": "error", "val": "You can only delete your own attachments"}`
- `{"cmd": "error", "val": "Failed to delete attachment"}`

## Notes

- Requires authentication.
- Only the uploader can delete their own attachments.
- Users with `owner` or `admin` roles can delete any attachment.
- Deleting an attachment removes both the file and its metadata.
- Messages containing the attachment will still reference it, but the file will be inaccessible.

## See Also

- [attachment_upload](attachment_upload.md) - Upload an attachment
- [attachment_get](attachment_get.md) - Get attachment info
