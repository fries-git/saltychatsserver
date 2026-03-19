# Command: embeds_list

**Request:**
```json
{
  "cmd": "embeds_list",
  "channel": "<channel_name>",
  "id": "<message_id>"
}
```

Or for thread messages:

```json
{
  "cmd": "embeds_list",
  "thread_id": "<thread_id>",
  "id": "<message_id>"
}
```

- `channel`: Channel name (required if not using `thread_id`).
- `thread_id`: Thread ID (required if not using `channel`).
- `id`: Message ID.

**Response:**
- On success:
```json
{
  "cmd": "embeds_list",
  "id": "<message_id>",
  "embeds": [ ...array of embed objects... ]
}
```

- On error: see [common errors](errors.md).

**Notes:**
- User must be authenticated and have access to the channel/thread.
- Returns an empty array if the message has no embeds.

See implementation: [`handlers/message.py`](../handlers/message.py) (search for `case "embeds_list":`).
