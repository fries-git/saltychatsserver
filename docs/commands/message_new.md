# Command: message_new

**Request:**
```json
{
  "cmd": "message_new",
  "channel": "<channel_name>",
  "thread_id": "<optional_thread_id>",
  "content": "<message_content>",
  "reply_to": "<optional_message_id>",
  "ping": true,
  "attachments": [
    {"id": "<attachment_id>"}
  ]
}
```

### Fields

- `channel`: Name of the channel to send the message to. Required unless `thread_id` is provided.
- `thread_id`: (Optional) ID of the thread to send the message to. If provided, message is sent to the thread instead of the channel.
- `content`: Message text (optional if attachments provided, trimmed, max length enforced by config).
- `reply_to`: (Optional) ID of the message being replied to.
- `ping`: (Optional) Whether to notify the user being replied to. Defaults to `true`. Only applies when using `reply_to`.
- `attachments`: (Optional) Array of attachment objects. Each object must have an `id` field with the attachment ID from `attachment_upload`.

**Response:**
- On success (channel message):
```json
{
  "cmd": "message_new",
  "message": {
    "id": "message-uuid",
    "user": "username",
    "content": "Message content here",
    "timestamp": 1773182676.073865,
    "type": "message",
    "pinned": false,
    "reply_to": {
      "id": "original-message-id",
      "user": "original-username"
    },
    "ping": true,
    "attachments": [
      {
        "id": "attachment-uuid",
        "name": "file.png",
        "mime_type": "image/png",
        "size": 12345,
        "url": "https://server.com/attachments/attachment-uuid",
        "expires_at": 1712345678.9,
        "permanent": false
      }
    ]
  },
  "channel": "<channel_name>",
  "global": true
}
```

- On success (thread message):
```json
{
  "cmd": "message_new",
  "message": {
    "id": "message-uuid",
    "user": "username",
    "content": "Message content here",
    "timestamp": 1773182676.073865,
    "type": "message",
    "pinned": false
  },
  "thread_id": "<thread_id>",
  "global": true
}
```

- On error: see [common errors](errors.md).

**Notes:**
- User must be authenticated and have permission to send in the channel.
- Rate limiting and message length are enforced.
- Replies include a `reply_to` field in the message object.
- The `ping` field controls whether a reply counts as a ping to the original message author:
  - If `ping` is `true` or not provided (default): The reply will be included in `pings_get` for the user being replied to
  - If `ping` is `false`: The reply will NOT be included in `pings_get` for the user being replied to
  - This allows users to reply without notifying/pinging the original poster
- The `ping` field is only included in the response if explicitly provided in the request; it defaults to `true` for `pings_get` lookups
- **Forum Channels:** Cannot send messages directly to forum channels. Use `thread_id` to send messages to threads within forum channels.
- **Thread Messages:** When sending to a thread, the thread must not be locked or archived.

### Attachments

To send a message with attachments:

1. Upload the file using `attachment_upload` command
2. Use the returned `attachment.id` in the `attachments` array
3. Send the message with `message_new`

Example workflow:
```json
// 1. Upload attachment
{"cmd": "attachment_upload", "file": "data:image/png;base64,...", "name": "image.png", "mime_type": "image/png", "channel": "general"}
// Response: {"cmd": "attachment_uploaded", "attachment": {"id": "abc-123", ...}}

// 2. Send message with attachment
{"cmd": "message_new", "channel": "general", "content": "Check this out!", "attachments": [{"id": "abc-123"}]}
```

**Attachment Notes:**
- Only attachments uploaded by the authenticated user can be attached to messages
- Once attached, the attachment is marked as "referenced" and won't be auto-deleted
- When a message with attachments is deleted, the attachments are also deleted
- Attachments expire based on file size (smaller = longer retention)

See implementation: [`handlers/message.py`](../handlers/message.py) (search for `case "message_new":`).
