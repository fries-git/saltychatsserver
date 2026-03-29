# poll_get

Get detailed information about a poll, including all options and your current votes.

## Request

```json
{
  "cmd": "poll_get",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Alternative: Use Message ID

```json
{
  "cmd": "poll_get",
  "message_id": "msg-uuid-here"
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poll_id` | string | Yes* | Poll UUID |
| `message_id` | string | Yes* | Message ID (alternative to poll_id) |

\* Either `poll_id` or `message_id` is required.

## Response

```json
{
  "cmd": "poll_get",
  "poll": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "msg-uuid-here",
    "channel": "general",
    "thread_id": null,
    "question": "What's your favorite language?",
    "options": [
      {"id": "python", "text": "Python", "emoji": "🐍"},
      {"id": "js", "text": "JavaScript", "emoji": "🟨"},
      {"id": "rust", "text": "Rust", "emoji": "🦀"}
    ],
    "allow_multiselect": false,
    "expires_at": 1704153600,
    "created_by": "alice",
    "created_at": 1704067200,
    "ended": false,
    "ended_at": null,
    "user_votes": ["python"]
  }
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Poll UUID |
| `message_id` | string | Message ID containing the poll |
| `channel` | string\|null | Channel name (null if in thread) |
| `thread_id` | string\|null | Thread ID (null if in channel) |
| `question` | string | Poll question |
| `options` | array | Array of poll options |
| `allow_multiselect` | boolean | Whether multiple votes allowed |
| `expires_at` | number\|null | Unix timestamp for expiration (null if no expiry) |
| `created_by` | string | Username of poll creator |
| `created_at` | number | Unix timestamp when created |
| `ended` | boolean | Whether poll has ended |
| `ended_at` | number\|null | Unix timestamp when ended (null if not ended) |
| `user_votes` | array | Array of option IDs the requesting user has voted for |

## Permissions

Requires `view` permission in the channel where the poll was posted.

## Example

```json
{
  "cmd": "poll_get",
  "message_id": "abc123"
}
```

## Errors

| Error | Description |
|-------|-------------|
| `poll_id or message_id is required` | Neither parameter provided |
| `Poll not found` | Invalid poll_id or message_id |
| `You do not have permission to view this poll` | Missing view permission |

## See Also

- [poll_create](poll_create.md) - Create a poll
- [poll_vote](poll_vote.md) - Vote on a poll
- [poll_end](poll_end.md) - End a poll
- [poll_results](poll_results.md) - Get poll results
- [Polls System](../polls.md)
