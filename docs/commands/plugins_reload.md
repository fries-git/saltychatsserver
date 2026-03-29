# Command: plugins_reload

Reload plugins. Requires `manage_server` permission.

## Permissions

- Requires `manage_server` permission.

**Request:**
```json
{
  "cmd": "plugins_reload",
  "plugin": "<optional_plugin_name>"
}
```

- `plugin`: (Optional) Name of a specific plugin to reload. If omitted, all plugins are reloaded.

**Response:**
- On success:
```json
{
  "cmd": "plugins_reload",
  "val": "...status message..."
}
```
- On error: see [common errors](errors.md).

**Notes:**
- User must be authenticated and have the `manage_server` permission.

See implementation: [`handlers/message.py`](../handlers/message.py) (search for `case "plugins_reload":`).
