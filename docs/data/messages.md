# Message Object Structure

A message object represents a chat message. Example structure:

```json
{
  "user": "alice",
  "content": "Hello, world!",
  "timestamp": 1722510000.123,
  "type": "message",
  "pinned": false,
  "id": "b1c2d3e4-5678-90ab-cdef-1234567890ab",
  "reply_to": {
    "id": "aabbccdd-1122-3344-5566-77889900aabb",
    "user": "bob"
  }
}
```

- `user`: Username of the sender. For webhook messages, this is `"originChats"`.
- `content`: Message text.
- `timestamp`: Unix timestamp (float).
- `type`: Always `message` for chat messages.
- `pinned`: Boolean, whether the message is pinned.
- `id`: Unique message ID (UUID string).
- `reply_to`: (Optional) Object with `id` and `user` of the replied-to message.
- `webhook`: (Optional) Object present only for webhook messages, containing:
  - `id`: The webhook's UUID
  - `name`: The webhook's display name (may include username override)
  - `avatar`: The webhook's avatar URL (may include avatar override)

Returned by: [messages_get](../commands/messages_get.md), [message_get](../commands/message_get.md)

## Webhook Messages

Messages from webhooks include a `webhook` object and show `user: "originChats"`:

```json
{
  "user": "originChats",
  "content": "New deployment complete!",
  "timestamp": 1722510000.123,
  "type": "message",
  "pinned": false,
  "id": "b1c2d3e4-5678-90ab-cdef-1234567890ab",
  "webhook": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "GitHub Actions",
    "avatar": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
  }
}
```
