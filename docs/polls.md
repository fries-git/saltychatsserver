# Polls System

OriginChats supports polls through the embeds system. Polls allow users to vote on options and see real-time results.

## Overview

Polls are a special type of embed that includes:
- A question
- Multiple choice options (2-10)
- Optional expiration time
- Optional multiselect (allow multiple votes)
- Real-time vote tracking

---

## Creating a Poll

### Using `poll_create`

Send a `poll_create` command to create a poll:

```json
{
  "cmd": "poll_create",
  "channel": "general",
  "question": "What's your favorite programming language?",
  "options": [
    {"id": "python", "text": "Python", "emoji": "🐍"},
    {"id": "js", "text": "JavaScript", "emoji": "🟨"},
    {"id": "rust", "text": "Rust", "emoji": "🦀"},
    {"id": "go", "text": "Go", "emoji": "🔵"}
  ],
  "allow_multiselect": false,
  "duration_hours": 24
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | Yes* | Channel to post poll in |
| `thread_id` | string | Yes* | Thread to post poll in (alternative to channel) |
| `question` | string | Yes | The poll question (max 300 chars) |
| `options` | array | Yes | Array of 2-10 options |
| `allow_multiselect` | boolean | No | Allow multiple votes (default: false) |
| `expires_at` | number | No | Unix timestamp when poll expires |
| `duration_hours` | number | No | Hours until poll expires (alternative to expires_at) |

\* Either `channel` or `thread_id` is required.

### Option Format

Options can be:
- Simple strings: `["Option 1", "Option 2"]`
- Objects with details:
  ```json
  {
    "id": "custom_id",
    "text": "Option text",
    "emoji": "🎯"
  }
  ```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Custom ID (auto-generated if omitted) |
| `text` | string | Yes | Option display text (max 100 chars) |
| `emoji` | string | No | Optional emoji for the option |

### Response

```json
{
  "cmd": "poll_create",
  "poll_id": "uuid-here",
  "message_id": "message-uuid",
  "channel": "general",
  "question": "What's your favorite programming language?",
  "options": [...],
  "allow_multiselect": false,
  "expires_at": 1234567890
}
```

---

## Voting on a Poll

### Using `poll_vote`

```json
{
  "cmd": "poll_vote",
  "poll_id": "uuid-here",
  "option_ids": ["python"]
}
```

For multiselect polls:
```json
{
  "cmd": "poll_vote",
  "poll_id": "uuid-here",
  "option_ids": ["python", "rust"]
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poll_id` | string | Yes* | Poll UUID |
| `message_id` | string | Yes* | Message ID (alternative to poll_id) |
| `option_ids` | array | Yes | Option ID(s) to vote for |
| `option_id` | string | Yes | Single option ID (alternative to option_ids) |

\* Either `poll_id` or `message_id` is required.

### Vote Behavior

- **Single-select polls**: Voting replaces your previous vote
- **Multiselect polls**: Each vote adds to your selections
- Voting on an already-selected option in multiselect mode removes that vote

### Response

```json
{
  "cmd": "poll_vote",
  "poll_id": "uuid-here",
  "option_ids": ["python"],
  "results": {
    "poll_id": "uuid-here",
    "question": "...",
    "total_votes": 5,
    "results": [
      {"id": "python", "text": "Python", "votes": 3, "voters": []},
      {"id": "js", "text": "JavaScript", "votes": 2, "voters": []},
      ...
    ]
  }
}
```

---

## Ending a Poll

### Using `poll_end`

Poll creators or users with `manage_messages` permission can end a poll early:

```json
{
  "cmd": "poll_end",
  "poll_id": "uuid-here"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poll_id` | string | Yes* | Poll UUID |
| `message_id` | string | Yes* | Message ID (alternative to poll_id) |

### Response

```json
{
  "cmd": "poll_end",
  "poll_id": "uuid-here",
  "results": {
    "poll_id": "uuid-here",
    "question": "...",
    "ended": true,
    "ended_at": 1234567890,
    "total_votes": 10,
    "results": [
      {"id": "python", "text": "Python", "votes": 6, "voters": ["user1", "user2", ...]},
      ...
    ]
  }
}
```

When a poll ends, the `voters` list becomes visible to everyone.

---

## Getting Poll Results

### Using `poll_results`

```json
{
  "cmd": "poll_results",
  "poll_id": "uuid-here"
}
```

### Response

```json
{
  "cmd": "poll_results",
  "poll_id": "uuid-here",
  "message_id": "message-uuid",
  "results": {
    "poll_id": "uuid-here",
    "question": "...",
    "allow_multiselect": false,
    "ended": false,
    "ended_at": null,
    "total_votes": 5,
    "results": [
      {"id": "python", "text": "Python", "votes": 3, "voted": true, "voters": []},
      {"id": "js", "text": "JavaScript", "votes": 2, "voted": false, "voters": []},
      ...
    ]
  }
}
```

The `voted` field indicates if the requesting user has voted for that option.

---

## Getting Poll Details

### Using `poll_get`

```json
{
  "cmd": "poll_get",
  "poll_id": "uuid-here"
}
```

### Response

```json
{
  "cmd": "poll_get",
  "poll": {
    "id": "uuid-here",
    "message_id": "message-uuid",
    "channel": "general",
    "thread_id": null,
    "question": "What's your favorite programming language?",
    "options": [
      {"id": "python", "text": "Python", "emoji": "🐍"},
      {"id": "js", "text": "JavaScript", "emoji": "🟨"},
      ...
    ],
    "allow_multiselect": false,
    "expires_at": 1234567890,
    "created_by": "username",
    "created_at": 1234567890,
    "ended": false,
    "ended_at": null,
    "user_votes": ["python"]
  }
}
```

---

## Poll Embed Format

Polls are stored as a special embed type:

```json
{
  "type": "poll",
  "title": "Poll Question",
  "poll": {
    "question": "What's your favorite programming language?",
    "options": [
      {"id": "python", "text": "Python", "emoji": "🐍"},
      {"id": "js", "text": "JavaScript", "emoji": "🟨"}
    ],
    "allow_multiselect": false,
    "expires_at": 1234567890
  }
}
```

---

## Real-time Updates

When a user votes, a broadcast is sent to all users viewing the channel:

```json
{
  "cmd": "poll_vote_update",
  "poll_id": "uuid-here",
  "message_id": "message-uuid",
  "channel": "general",
  "user": "username",
  "option_ids": ["python"],
  "results": {...}
}
```

When a poll ends:

```json
{
  "cmd": "poll_end",
  "poll_id": "uuid-here",
  "message_id": "message-uuid",
  "channel": "general",
  "results": {...}
}
```

---

## Permissions

| Action | Permission Required |
|--------|-------------------|
| Create poll | `send_messages` in channel |
| Vote on poll | `view` permission in channel |
| End poll | Poll creator OR `manage_messages` |
| View results | `view` permission in channel |

---

## Limits

| Limit | Value |
|-------|-------|
| Question length | 300 characters |
| Options per poll | 2-10 |
| Option text length | 100 characters |
| Option ID length | 50 characters |
| Total embed chars | 6000 characters |

---

## Examples

### Simple Poll

```json
{
  "cmd": "poll_create",
  "channel": "general",
  "question": "Pizza or Tacos?",
  "options": ["Pizza 🍕", "Tacos 🌮"]
}
```

### Timed Poll with Expiration

```json
{
  "cmd": "poll_create",
  "channel": "announcements",
  "question": "Should we change the server icon?",
  "options": [
    {"id": "yes", "text": "Yes, change it"},
    {"id": "no", "text": "No, keep current"},
    {"id": "maybe", "text": "I don't care"}
  ],
  "duration_hours": 48
}
```

### Multiselect Poll

```json
{
  "cmd": "poll_create",
  "channel": "general",
  "question": "Which events should we host? (Select all that apply)",
  "options": [
    "Game Night 🎮",
    "Movie Night 🎬",
    "Music Listening Party 🎵",
    "Art Showcase 🎨"
  ],
  "allow_multiselect": true
}
```

---

**See Also:**
- [Embed Types](embeds.md)
- [Permissions](permissions.md)
- [Messages](commands/message_new.md)
