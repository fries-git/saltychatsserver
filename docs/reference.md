# Reference

Data structures and formats used in OriginChats.

---

## User Object

```json
{
  "username": "alice",
  "roles": ["user", "moderator"],
  "id": "USR:1234567890abcdef"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Display name |
| `roles` | array | List of role names |
| `id` | string | Unique user ID from Rotur |

### User Connection Broadcasts

**user_join** - When a user joins for the first time:

```json
{
  "cmd": "user_join",
  "user": {
    "username": "alice",
    "roles": ["user", "moderator"],
    "color": "#00aaff"
  }
}
```

**user_connect** - When a user connects (any session):

```json
{
  "cmd": "user_connect",
  "user": {
    "username": "alice",
    "roles": ["user", "moderator"],
    "color": "#00aaff"
  }
}
```

**user_disconnect** - When a user disconnects:

```json
{
  "cmd": "user_disconnect",
  "username": "alice"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `color` | string | Hex color of user's primary role |

---

## Message Object

```json
{
  "id": "msg-uuid-1234",
  "user": "alice",
  "content": "Hello world!",
  "timestamp": 1234567890.123,
  "type": "message",
  "pinned": false,
  "reply_to": {
    "id": "original-msg-id",
    "user": "bob"
  },
  "reactions": {
    "👍": ["alice", "bob"],
    "❤️": ["charlie"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique message ID |
| `user` | string | Username of sender |
| `content` | string | Message text |
| `timestamp` | number | Unix timestamp (seconds) |
| `type` | string | Always `"message"` |
| `pinned` | boolean | Whether message is pinned |
| `reply_to` | object | Original message if replying |
| `reactions` | object | Emoji → array of usernames |

### Reply Object

```json
{
  "id": "original-msg-id",
  "user": "bob"
}
```

---

## Channel Object

```json
{
  "name": "general",
  "type": "text",
  "position": 0,
  "permissions": {
    "user": ["view", "send"],
    "moderator": ["view", "send", "delete"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Channel name |
| `type` | string | `"text"`, `"voice"`, or `"forum"` |
| `position` | number | Order in channel list |
| `permissions` | object | Role → permission array |

### Channel Types

| Type | Description |
|------|-------------|
| `text` | Real-time text messaging |
| `voice` | Audio calls (WebRTC) |
| `forum` | Organized threads for topics |

### Permissions

| Permission | Description |
|------------|-------------|
| `view` | Can see the channel |
| `send` | Can send messages |
| `edit_own` | Can edit own messages |
| `delete` | Can delete any message |
| `pin` | Can pin messages |
| `react` | Can add reactions |

---

## Thread Object

```json
{
  "id": "thread-uuid-123",
  "title": "Question about setup",
  "creator": "alice",
  "channel": "forum-general",
  "created_at": 1234567890.123,
  "locked": false,
  "archived": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique thread ID |
| `title` | string | Thread title |
| `creator` | string | Username who created it |
| `channel` | string | Parent forum channel |
| `created_at` | number | Unix timestamp |
| `locked` | boolean | No new messages allowed |
| `archived` | boolean | Thread is archived |

---

## Role Object

```json
{
  "name": "moderator",
  "color": "#00aaff",
  "permissions": ["view", "send", "delete"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Role name |
| `color` | string | Hex color for display |
| `permissions` | array | List of permissions |

---

## Emoji Object

```json
{
  "id": "emoji-uuid-123",
  "name": "party",
  "filename": "party.gif",
  "uploaded_by": "alice"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique emoji ID |
| `name` | string | Emoji shortcode (without `:`) |
| `filename` | string | Image filename |
| `uploaded_by` | string | Username who uploaded |

---

## Voice Participant

```json
{
  "id": "USR:123",
  "username": "alice",
  "peer_id": "webrtc-peer-id",
  "muted": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | User ID |
| `username` | string | Username |
| `peer_id` | string | WebRTC peer ID |
| `muted` | boolean | Microphone muted |

Note: `peer_id` is only sent to channel participants, not viewers.

---

## Webhook Object

```json
{
  "id": "webhook-uuid",
  "name": "My Bot",
  "channel": "general",
  "token": "secret-token",
  "created_by": "alice"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Webhook ID |
| `name` | string | Display name |
| `channel` | string | Target channel |
| `token` | string | Secret token for auth |
| `created_by` | string | Creator username |

---

## Slash Command Schema

```json
{
  "name": "ban",
  "description": "Ban a user",
  "options": [
    {
      "name": "user",
      "type": "string",
      "description": "Username to ban",
      "required": true
    },
    {
      "name": "reason",
      "type": "string",
      "description": "Ban reason",
      "required": false
    }
  ],
  "whitelistRoles": ["moderator", "owner"]
}
```

### Option Types

| Type | Description |
|------|-------------|
| `string` | Text value |
| `integer` | Whole number |
| `boolean` | true/false |
| `user` | User mention |
| `channel` | Channel mention |

---

## Error Response

```json
{
  "cmd": "error",
  "val": "User not authenticated",
  "src": "message_new"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cmd` | string | Always `"error"` |
| `val` | string | Error message |
| `src` | string | Command that caused error |

---

## Rate Limit Response

```json
{
  "cmd": "rate_limit",
  "length": 5000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cmd` | string | Always `"rate_limit"` |
| `length` | number | Wait time in milliseconds |

---

## Ping Object

```json
{
  "id": "ping-uuid",
  "type": "reply",
  "channel": "general",
  "message_id": "msg-uuid",
  "from_user": "bob",
  "timestamp": 1234567890.123
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Ping ID |
| `type` | string | `"reply"`, `"mention"`, etc. |
| `channel` | string | Channel name |
| `message_id` | string | Related message ID |
| `from_user` | string | Who sent it |
| `timestamp` | number | When it happened |

---

## Embed Object

```json
{
  "type": "link",
  "url": "https://example.com",
  "title": "Example Site",
  "description": "A sample website",
  "image": "https://example.com/og.png"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `"link"`, `"image"`, `"video"` |
| `url` | string | Content URL |
| `title` | string | Display title |
| `description` | string | Description text |
| `image` | string | Preview image URL |

---

## Status Object

```json
{
  "status": "online",
  "custom": "😊 Feeling great!"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"online"`, `"away"`, `"dnd"`, `"offline"` |
| `custom` | string | Custom status message |

---

## See Also

- [Getting Started](getting-started.md) - Connection flow
- [Commands](commands/) - All available commands
- [Config](config.md) - Configuration options
