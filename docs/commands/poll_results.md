# poll_results

Get the current results of a poll, including vote counts and whether you have voted.

## Request

```json
{
  "cmd": "poll_results",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Alternative: Use Message ID

```json
{
  "cmd": "poll_results",
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
  "cmd": "poll_results",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "msg-uuid-here",
  "results": {
    "poll_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What's your favorite language?",
    "allow_multiselect": false,
    "ended": false,
    "ended_at": null,
    "total_votes": 15,
    "results": [
      {
        "id": "python",
        "text": "Python",
        "emoji": "🐍",
        "votes": 10,
        "voted": true,
        "voters": []
      },
      {
        "id": "js",
        "text": "JavaScript",
        "emoji": "🟨",
        "votes": 5,
        "voted": false,
        "voters": []
      }
    ]
  }
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `voted` | boolean | Whether the requesting user has voted for this option |
| `voters` | array | Empty if poll is active; contains usernames if ended |

## Permissions

Requires `view` permission in the channel where the poll was posted.

## Behavior

- For **active polls**: `voters` array is empty (privacy)
- For **ended polls**: `voters` array contains usernames of who voted
- `voted` field shows if you have voted for each option

## Example

```json
{
  "cmd": "poll_results",
  "poll_id": "abc123"
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
- [poll_get](poll_get.md) - Get poll details
- [Polls System](../polls.md)
