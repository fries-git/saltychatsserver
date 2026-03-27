# Creating Plugins

How to create plugins for OriginChats.

---

## What are Plugins?

Plugins are Python scripts that run on the server. They can:
- Respond to messages
- Handle user events (join, leave)
- Add custom slash commands
- Modify data before it's sent

---

## Plugin Structure

Every plugin needs a `getInfo()` function:

```python
def getInfo():
    return {
        "name": "My Plugin",
        "description": "What this plugin does",
        "handles": ["new_message", "user_join"]
    }
```

The `handles` field tells the server which events your plugin responds to.

---

## Events You Can Handle

| Event | When it fires |
|-------|---------------|
| `new_message` | When a message is sent |
| `user_join` | When a user joins for the first time |
| `user_connect` | When a user connects (any session) |
| `user_disconnect` | When a user disconnects |
| `typing` | When a user starts typing |
| `slash_call` | When a slash command is called |
| `message_edit` | When a message is edited |
| `message_delete` | When a message is deleted |
| `message_pin` | When a message is pinned |
| `message_unpin` | When a message is unpinned |
| `auto_moderate` | When automod takes action |

Plugins hook into these events and can execute custom logic when they fire.

---

## Example 1: Simple Responder

A plugin that responds to specific words:

```python
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.websocket_utils import broadcast_to_all
from logger import Logger

def getInfo():
    return {
        "name": "Auto Responder",
        "description": "Responds to !hello command",
        "handles": ["new_message"]
    }

async def on_new_message(ws, message_data, server_data):
    content = message_data.get("content", "")
    channel = message_data.get("channel")
    
if content.strip() == "!hello":
    await send_bot_message(channel, "Hello there!", server_data)

async def send_bot_message(channel, content, server_data):
    import uuid
    import time

    message = {
        "user": "originChats",
        "content": content,
        "timestamp": time.time(),
        "id": str(uuid.uuid4())
    }

    from db import channels
    channels.save_channel_message(channel, message)

    broadcast_msg = {
        "cmd": "message_new",
        "message": message,
        "channel": channel,
        "global": True
    }

    if server_data and "connected_clients" in server_data:
        await broadcast_to_all(server_data["connected_clients"], broadcast_msg)
```

Save as `plugins/my_plugin.py` and restart the server.

---

## Example 2: Welcome Plugin

Send a welcome message when users join:

```python
import os
import sys
import uuid
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import channels
from handlers.websocket_utils import broadcast_to_all
from logger import Logger

def getInfo():
    return {
        "name": "Welcome Bot",
        "description": "Welcomes new users",
        "handles": ["user_join"]
    }

async def on_user_join(ws, message_data, server_data):
    username = message_data.get("username")
    user_id = message_data.get("user_id")
    
if not username:
        return

    # Create welcome message
    message = {
        "user": "originChats",
        "content": f"Welcome {username}! 🎉",
        "timestamp": time.time(),
        "id": str(uuid.uuid4())
    }
    
    # Save and broadcast
    channel = "general"
    channels.save_channel_message(channel, message)
    
    broadcast_msg = {
        "cmd": "message_new",
        "message": message,
        "channel": channel,
        "global": True
    }
    
    if server_data and "connected_clients" in server_data:
        await broadcast_to_all(server_data["connected_clients"], broadcast_msg)
    
    Logger.info(f"Welcomed user {username}")
```

---

## Example 3: AutoMod Plugin

Block specific words:

```python
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import channels, users
from handlers.websocket_utils import broadcast_to_all, send_to_client
from logger import Logger

BLOCKED_WORDS = ["badword1", "badword2"]

def getInfo():
    return {
        "name": "Simple AutoMod",
        "description": "Blocks bad words",
        "handles": ["new_message"]
    }

async def on_new_message(ws, message_data, server_data):
    content = message_data.get("content", "").lower()
    channel = message_data.get("channel")
    message_id = message_data.get("message", {}).get("id")
    user_id = message_data.get("user_id")
    
    # Check for blocked words
    for word in BLOCKED_WORDS:
        if word in content:
            # Delete the message
            if message_id:
                channels.delete_channel_message(channel, message_id)
                
                # Broadcast deletion
                delete_msg = {
                    "cmd": "message_delete",
                    "id": message_id,
                    "channel": channel,
                    "global": True
                }
                await broadcast_to_all(
                    server_data["connected_clients"],
                    delete_msg
                )
            
            # Notify the user
            await send_to_client(ws, {
                "cmd": "error",
                "val": "Your message was removed (contains blocked word)"
            })
            
            Logger.warning(f"Blocked message from user {user_id}")
            break
```

---

## Message Data Structure

When handling `new_message`, you receive:

```python
{
    "user_id": "USR:123...",
    "username": "alice",
    "channel": "general",
    "content": "Hello world",
    "message": {
        "id": "msg-uuid",
        "user": "alice",
        "content": "Hello world",
        "timestamp": 1234567890.123
    }
}
```

---

## User Event Data

When handling `user_join`:

```python
{
    "user_id": "USR:123...",
    "username": "alice"
}
```

When handling `user_leave`:

```python
{
    "user_id": "USR:123...",
    "username": "alice"
}
```

---

## Slash Commands in Plugins

Plugins can handle custom slash commands:

```python
def getInfo():
    return {
        "name": "Dice Roller",
        "description": "Roll dice with /roll",
        "handles": ["slash_call"]
    }

async def on_slash_call(ws, data, server_data):
    command = data.get("val", {}).get("command")
    
    if command == "roll":
        import random
        result = random.randint(1, 6)
        
        return {
            "cmd": "slash_response",
            "channel": data.get("channel"),
            "response": f"🎲 You rolled a {result}!",
            "invoker": data.get("invoker"),
            "command": "roll"
        }
```

Users register the command first:
```json
{
  "cmd": "slash_register",
  "name": "roll",
  "description": "Roll a dice"
}
```

---

## Permission Checking

Check if user has permission:

```python
from db import users

def has_permission(user_id, required_roles):
    user_roles = users.get_user_roles(user_id)
    return any(role in user_roles for role in required_roles)

# Usage
if has_permission(user_id, ["owner", "admin"]):
    # Allow action
    pass
```

---

## Configuration

Plugins can have config files:

```python
import json
import os

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "my_plugin_config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "enabled": True,
            "setting1": "default"
        }

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), "my_plugin_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
```

---

## Logging

Use the server's logger:

```python
from logger import Logger

Logger.info("Plugin message")
Logger.warning("Warning message")
Logger.error("Error message")
Logger.success("Success message")
```

---

## Installing Plugins

1. Create your plugin file in `plugins/`
2. Restart the server
3. Plugin loads automatically

To disable a plugin:
- Move it to `disabled plugins/` folder
- Or rename it to start with `_` (e.g., `_my_plugin.py`)

---

## Best Practices

1. **Handle errors** - Wrap risky code in try/except
2. **Check permissions** - Don't let regular users do admin actions
3. **Don't block** - Use async functions, don't do heavy processing
4. **Log actions** - Use Logger so admins can see what happened
5. **Make configurable** - Let admins customize behavior via config files

---

## Example: Full Plugin

A complete, working plugin:

```python
import os
import sys
import json
import uuid
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import channels, users
from handlers.websocket_utils import broadcast_to_all
from logger import Logger

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "motd_config.json")

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "enabled": True,
            "motd": "Welcome to the server!",
            "show_on_join": True
        }

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def getInfo():
    return {
        "name": "MOTD Plugin",
        "description": "Shows message of the day when users join",
        "handles": ["user_join", "new_message"]
    }

async def on_user_join(ws, message_data, server_data):
    config = load_config()
    
    if not config.get("show_on_join", True):
        return
    
    await send_motd(message_data.get("username"), server_data)

async def on_new_message(ws, message_data, server_data):
    content = message_data.get("content", "").strip()
    user_id = message_data.get("user_id")
    
    # Admin can change MOTD
    if content.startswith("!motd "):
        user_roles = users.get_user_roles(user_id)
        if "owner" in user_roles or "admin" in user_roles:
            new_motd = content[6:].strip()
            config = load_config()
            config["motd"] = new_motd
            save_config(config)
            
            await send_to_channel(
                message_data.get("channel"),
                f"MOTD updated to: {new_motd}",
                server_data
            )

async def send_motd(username, server_data):
    config = load_config()
    motd = config.get("motd", "Welcome!")

    message = {
        "user": "originChats",
        "content": motd,
        "timestamp": time.time(),
        "id": str(uuid.uuid4())
    }

    channels.save_channel_message("general", message)

    broadcast_msg = {
        "cmd": "message_new",
        "message": message,
        "channel": "general",
        "global": True
    }

    if server_data and "connected_clients" in server_data:
        await broadcast_to_all(server_data["connected_clients"], broadcast_msg)

async def send_to_channel(channel, content, server_data):
    message = {
        "user": "originChats",
        "content": content,
        "timestamp": time.time(),
        "id": str(uuid.uuid4())
    }
    
    channels.save_channel_message(channel, message)
    
    broadcast_msg = {
        "cmd": "message_new",
        "message": message,
        "channel": channel,
        "global": True
    }
    
    if server_data and "connected_clients" in server_data:
        await broadcast_to_all(server_data["connected_clients"], broadcast_msg)
```

---

## See Also

- [Existing Plugins](../plugins/) - See how other plugins work
- [Welcome Plugin](plugins/welcome.md) - Welcome message plugin docs
- [Server README](../README.md) - Server setup
