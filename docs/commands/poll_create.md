# poll_create

Create a new poll in a channel or thread.

## Request

```json
{
  "cmd": "poll_create",
  "channel": "general",
  "question": "What's your favorite color?",
  "options": [
    {"id": "red", "text": "Red 🔴"},
    {"id": "blue", "text": "Blue 🔵"},
    {"id": "green", "text": "Green 🟢"}
  ],
  "allow_multiselect": false,
  "duration_hours": 24
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | Yes* | Channel name to post poll in |
| `thread_id` | string | Yes* | Thread ID to post poll in (alternative to channel) |
| `question` | string | Yes | Poll question (max 300 chars) |
| `options` | array | Yes | Array of 2-10 poll options |
| `allow_multiselect` | boolean | No | Allow multiple votes (default: false) |
| `expires_at` | number | No | Unix timestamp when poll expires |
| `duration_hours` | number | No | Hours until expiration (alternative to expires_at) |

\* Either `channel` or `thread_id` is required.

## Options Format

Each option can be:

**Simple string:**
```json
["Option 1", "Option 2"]
```

**Object with details:**
```json
[
  {"id": "opt1", "text": "Option 1", "emoji": "👍"},
  {"id": "opt2", "text": "Option 2", "emoji": "👎"}
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Custom ID (auto-generated if omitted, max 50 chars) |
| `text` | string | Yes | Option text (max 100 chars) |
| `emoji` | string | No | Optional emoji |

## Response

```json
{
  "cmd": "poll_create",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "msg-uuid-here",
  "channel": "general",
  "thread_id": null,
  "question": "What's your favorite color?",
  "options": [
    {"id": "red", "text": "Red 🔴"},
    {"id": "blue", "text": "Blue 🔵"},
    {"id": "green", "text": "Green 🟢"}
  ],
  "allow_multiselect": false,
  "expires_at": 1704067200
}
```

## Permissions

Requires `send_messages` permission in the target channel.

## Limits

| Limit | Value |
|-------|-------|
| Question length | 300 characters |
| Options per poll | 2-10 |
| Option text length | 100 characters |
| Option ID length | 50 characters |

## Example

### Simple Poll

```json
{
  "cmd": "poll_create",
  "channel": "general",
  "question": "Pizza or Tacos?",
  "options": ["Pizza 🍕", "Tacos 🌮"]
}
```

### Multi-select Poll with Expiration

```json
{
  "cmd": "poll_create",
  "channel": "announcements",
  "question": "Which features should we prioritize?",
  "options": [
    {"id": "dark", "text": "Dark mode"},
    {"id": "notif", "text": "Better notifications"},
    {"id": "search", "text": "Improved search"},
    {"id": "mobile", "text": "Mobile app"}
  ],
  "allow_multiselect": true,
  "duration_hours": 48
}
```

## Errors

| Error | Description |
|-------|-------------|
| `Channel or thread_id is required` | Neither parameter provided |
| `Question is required` | Missing question |
| `At least 2 options are required` | Less than 2 options provided |
| `Cannot have more than 10 options` | More than 10 options provided |
| `Channel not found` | Invalid channel name |
| `You do not have permission to send messages` | Missing send_messages permission |

## See Also

- [poll_vote](poll_vote.md) - Vote on a poll
- [poll_end](poll_end.md) - End a poll
- [poll_results](poll_results.md) - Get poll results
- [poll_get](poll_get.md) - Get poll details
- [Polls System](../polls.md)
