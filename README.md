# OriginChats

A real-time chat server with text, voice, and forum channels.

## Features

- **Text Channels** - Send messages, reply, react, pin
- **Voice Channels** - Peer-to-peer audio calls
- **Forum Channels** - Organized threads for discussions
- **User Management** - Roles, permissions, bans, timeouts
- **Plugins** - Extend with custom features
- **Slash Commands** - Custom commands for users

## Quick Start

1. **Install:**
```bash
pip install -r requirements.txt
```

2. **Configure:**
```bash
python setup.py
```

3. **Run:**
```bash
python init.py
```

Server runs at `ws://localhost:5613` by default.

## Documentation

- **[Overview](docs/overview.md)** - Core concepts and features
- **[Getting Started](docs/getting-started.md)** - How to connect and use the API
- **[Client Development](docs/clients.md)** - Build your own client
- **[Plugin Development](docs/plugins.md)** - Create server plugins
- **[Production Setup](docs/production.md)** - Deploy securely
- **[Command Reference](docs/commands/)** - All available commands
- **[Clients](clients.md)** - Existing clients you can use

## Configuration

Main settings in `config.json`:

```json
{
  "websocket": { "host": "127.0.0.1", "port": 5613 },
  "rate_limiting": { "enabled": true, "messages_per_minute": 30 },
  "limits": { "post_content": 2000 }
}
```

See [Configuration Docs](docs/config.md) for all options.

## Rate Limiting

Built-in spam protection limits messages per user. When rate limited, clients receive:

```json
{ "cmd": "rate_limit", "length": 5000 }
```

Wait `length` milliseconds before sending more messages.

## Channel Types

| Type | Description |
|------|-------------|
| **Text** | Real-time text messaging |
| **Voice** | Audio calls via WebRTC |
| **Forum** | Organized threads for topics |

## Permissions

Role-based permissions control what users can do:
- View channels
- Send/edit/delete messages
- Manage users (ban, timeout)
- Pin messages
- Use slash commands

See [Permissions](docs/data/permissions.md) for details.

## Authentication

Uses Rotur authentication service. See [Getting Started](docs/getting-started.md) for the full flow.

## Clients

See [clients.md](clients.md) for available clients.

## Development

### Adding New Commands

1. Add a new case in [`handlers/message.py`](handlers/message.py):
   ```python
   case "my_command":
       # Handle command
       return {"cmd": "my_response"}
   ```

2. Update documentation in `docs/commands/my_command.md`

### Creating Plugins

See `plugins/` directory for examples. Plugins can:
- Respond to new messages
- Handle slash commands
- Modify message data
- Trigger events

### Adding Config Values

Use the same 3-step flow throughout the codebase:

1. Add the default in `config_builder.py`.
2. If it should be configurable during setup, prompt for it in `setup.py` and add it to the overrides passed into `build_config(...)`.
3. Read it with `get_config_value(...)` from `config_store.py`, or use the local handler helper when `server_data["config"]` is already available.

## API Protocol

All WebSocket messages follow this format:

```json
{
  "cmd": "command_name",
  "key": "value",
  "global": true  // Optional: broadcast to all
}
```

See [Protocol Documentation](docs/protocol.md) for details.

## Error Handling

All errors return:

```json
{
  "cmd": "error",
  "val": "Error message"
}
```

See [Error Handling](docs/errors.md) for all possible errors.

## Contributing

Contributions welcome! See the [documentation](docs/) for details.

