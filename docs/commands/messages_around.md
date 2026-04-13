# Command: messages_around

Retrieve messages centered around a specific message ID.

## Request

```json
{
  "cmd": "messages_around",
  "channel": "<channel_name>",
  "around": "<message_id>",
  "bounds": {
    "above": <optional_count>,
    "below": <optional_count>
  }
}
```

Or for threads:

```json
{
  "cmd": "messages_around",
  "thread_id": "<thread_id>",
  "around": "<message_id>",
  "bounds": {
    "above": <optional_count>,
    "below": <optional_count>
  }
}
```

### Fields

- `channel`: (required if not using `thread_id`) Name of the text channel.
- `thread_id`: (required if not using `channel`) ID of the thread.
- `around`: (required) Message ID to center the retrieval around.
- `bounds`: (optional) Number of messages to include around the target.
  - `above`: Messages after (newer than) the target. Default: `50`, Max: `200`
  - `below`: Messages before (older than) the target. Default: `50`, Max: `200`

## Response

### On Success

```json
{
  "cmd": "messages_around",
  "channel": "<channel_name>",
  "messages": [
    {
      "user": "alice",
      "content": "Hello!",
      "timestamp": 1722510000.123,
      "type": "message",
      "pinned": false,
      "id": "b1c2d3e4-5678-90ab-cdef-1234567890ab"
    },
    // ... more messages
  ],
  "range": {
    "start": 100,
    "end": 201
  }
}
```

For thread messages:

```json
{
  "cmd": "messages_around",
  "channel": "<channel_name>",
  "thread_id": "<thread_id>",
  "messages": [
    {
      "user": "alice",
      "content": "Hello!",
      "timestamp": 1722510000.123,
      "type": "message",
      "pinned": false,
      "id": "b1c2d3e4-5678-90ab-cdef-1234567890ab"
    },
    // ... more messages
  ],
  "range": {
    "start": 10,
    "end": 61
  }
}
```

- **Messages are returned in chronological order** (oldest first)
- The target message is included in the results
- `range.start` and `range.end` indicate the 0-indexed positions in the channel/thread

## Usage Examples

### Get Context Around a Message (Default Bounds)

```json
{
  "cmd": "messages_around",
  "channel": "general",
  "around": "b1c2d3e4-5678-90ab-cdef-1234567890ab"
}
// Returns up to 101 messages (50 below + target + 50 above)
```

### Get Messages Around a Specific Message with Custom Bounds

```json
{
  "cmd": "messages_around",
  "channel": "general",
  "around": "b1c2d3e4-5678-90ab-cdef-1234567890ab",
  "bounds": {
    "above": 25,
    "below": 25
  }
}
// Returns up to 51 messages (25 below + target + 25 above)
```

### Get Thread Messages Around a Message

```json
{
  "cmd": "messages_around",
  "thread_id": "thread-12345",
  "around": "b1c2d3e4-5678-90ab-cdef-1234567890ab",
  "bounds": {
    "above": 10,
    "below": 10
  }
}
// Returns up to 21 messages from the thread
```

## Error Responses

- `{"cmd": "error", "val": "around (message ID) is required"}`
- `{"cmd": "error", "val": "Invalid channel name"}`
- `{"cmd": "error", "val": "Channel not found"}`
- `{"cmd": "error", "val": "Thread not found"}`
- `{"cmd": "error", "val": "Access denied to this channel"}`
- `{"cmd": "error", "val": "User not authenticated"}`
- `{"cmd": "error", "val": "Message not found"}`

## Notes

- User must be authenticated.
- User must have `view` permission on the channel/thread.
- Only works on **text channels** (not voice channels).
- Cannot access messages in locked or archived threads.
- If bounds exceed available messages, returns what's available (no error).
- Bounds are capped at 200 each.
- Useful for jumping to a specific message (e.g., from a notification or search result).

## See Also

- [messages_get](messages_get.md) - Get messages with pagination
- [message_get](message_get.md) - Get a specific message by ID
- [messages_search](messages_search.md) - Search for messages

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "messages_around":`).
