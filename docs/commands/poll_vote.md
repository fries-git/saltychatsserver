# poll_vote

Vote on a poll. For single-select polls, voting replaces your previous vote. For multiselect polls, each vote adds to your selections.

## Request

### Single Vote

```json
{
  "cmd": "poll_vote",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "option_ids": ["python"]
}
```

### Alternative: Single Option

```json
{
  "cmd": "poll_vote",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "option_id": "python"
}
```

### Multiple Votes (Multiselect)

```json
{
  "cmd": "poll_vote",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "option_ids": ["python", "rust"]
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poll_id` | string | Yes* | Poll UUID |
| `message_id` | string | Yes* | Message ID (alternative to poll_id) |
| `option_ids` | array | Yes** | Array of option IDs to vote for |
| `option_id` | string | Yes** | Single option ID (alternative to option_ids) |

\* Either `poll_id` or `message_id` is required.
\** Either `option_ids` or `option_id` is required.

## Response

```json
{
  "cmd": "poll_vote",
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "option_ids": ["python"],
  "results": {
    "poll_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What's your favorite language?",
    "allow_multiselect": false,
    "ended": false,
    "ended_at": null,
    "total_votes": 5,
    "results": [
      {"id": "python", "text": "Python", "votes": 3, "voters": []},
      {"id": "js", "text": "JavaScript", "votes": 2, "voters": []}
    ]
  }
}
```

## Permissions

Requires `view` permission in the channel where the poll was posted.

## Behavior

- **Single-select polls**: Voting replaces your previous vote
- **Multiselect polls**: Each call adds options to your selections
- Voting for an already-selected option in multiselect mode removes that vote
- Cannot vote on ended polls
- Cannot vote on expired polls

## Example

```json
{
  "cmd": "poll_vote",
  "poll_id": "abc123",
  "option_ids": ["yes"]
}
```

## Errors

| Error | Description |
|-------|-------------|
| `poll_id or message_id is required` | Neither parameter provided |
| `option_id or option_ids is required` | Neither parameter provided |
| `Poll not found` | Invalid poll_id or message_id |
| `Poll has ended` | Poll is already ended |
| `Poll has expired` | Poll expiration time has passed |
| `Invalid option: xyz` | Option ID doesn't exist in poll |
| `You do not have permission to view this poll` | Missing view permission |

## See Also

- [poll_create](poll_create.md) - Create a poll
- [poll_end](poll_end.md) - End a poll
- [poll_results](poll_results.md) - Get poll results
- [poll_get](poll_get.md) - Get poll details
- [Polls System](../polls.md)
