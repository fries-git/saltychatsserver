# poll_end

End a poll manually. Only the poll creator or users with `manage_messages` permission can end a poll.

## Request

```json
{
  "cmd": "poll_end",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Alternative: Use Message ID

```json
{
  "cmd": "poll_end",
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
  "cmd": "poll_end",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": {
    "poll_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What's your favorite language?",
    "allow_multiselect": false,
    "ended": true,
    "ended_at": 1704067200,
    "total_votes": 15,
    "results": [
      {
        "id": "python", 
        "text": "Python", 
        "votes": 10, 
        "voters": ["alice", "bob", "charlie"]
      },
      {
        "id": "js", 
        "text": "JavaScript", 
        "votes": 5, 
        "voters": ["dave", "eve"]
      }
    ]
  }
}
```

## Permissions

- **Poll creator**: Can always end their own poll
- **Other users**: Requires `manage_messages` permission

## Behavior

- When a poll ends, all voters' usernames become visible in results
- Ended polls cannot receive more votes
- Ending an already-ended poll returns an error
- A broadcast is sent to all users in the channel

## Example

```json
{
  "cmd": "poll_end",
  "poll_id": "abc123"
}
```

## Errors

| Error | Description |
|-------|-------------|
| `poll_id or message_id is required` | Neither parameter provided |
| `Poll not found` | Invalid poll_id or message_id |
| `Poll has already ended` | Poll was previously ended |
| `Access denied: 'manage_messages' permission required` | Not creator and lacks permission |

## See Also

- [poll_create](poll_create.md) - Create a poll
- [poll_vote](poll_vote.md) - Vote on a poll
- [poll_results](poll_results.md) - Get poll results
- [Polls System](../polls.md)
