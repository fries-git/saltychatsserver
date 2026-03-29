# Command: plugins_list

List all loaded plugins. Requires `manage_server` permission.

## Permissions

- Requires `manage_server` permission.

**Request:**
```json
{"cmd": "plugins_list"}
```

**Response:**
- On success:
```json
{
  "cmd": "plugins_list",
  "plugins": [ ...array of plugin names... ]
}
```
- On error: see [common errors](errors.md).

**Notes:**
- User must be authenticated and have the `manage_server` permission.

See implementation: [`handlers/message.py`](../handlers/message.py) (search for `case "plugins_list":`).
