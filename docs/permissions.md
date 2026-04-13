# Permissions System

OriginChats uses a centralized permission system that allows fine-grained control over what users can do on the server.

## Overview

The permission system replaces the previous "owner-only" approach with a flexible role-based access control (RBAC) system. Permissions are stored on roles and checked centrally, while channels can implement additional restrictions.

### Key Concepts

- **Permissions are granted to roles** - Users inherit permissions from their assigned roles
- **Role hierarchy is enforced** - Users can only manage roles below their highest role
- **Owner has full access** - The owner role bypasses all permission checks
- **Administrator permission** - Roles with `administrator` bypass most checks
- **Channel overrides** - Channels can deny specific permissions

---

## Available Permissions

### Server Management

| Permission | Description |
|------------|-------------|
| `administrator` | Full permissions (bypasses all checks except owner) |
| `manage_server` | Update server settings, emojis, and webhooks |
| `view_audit_log` | View server audit logs |

### Role Management

| Permission | Description |
|------------|-------------|
| `manage_roles` | Create, delete, and assign roles below own position |

### Channel Management

| Permission | Description |
|------------|-------------|
| `manage_channels` | Create, delete, and configure channels |
| `manage_threads` | Lock, archive, and delete threads |

### User Moderation

| Permission | Description |
|------------|-------------|
| `manage_users` | Ban, unban, timeout, and manage user nicknames |
| `kick_members` | Kick users from the server |
| `manage_nicknames` | Change other users' nicknames |
| `change_nickname` | Change own nickname |

### Voice Channels

| Permission | Description |
|------------|-------------|
| `connect` | Connect to voice channels |
| `speak` | Speak in voice channels |
| `stream` | Stream video in voice channels |
| `mute_members` | Mute users in voice channels |
| `deafen_members` | Deafen users in voice channels |
| `move_members` | Move users between voice channels |
| `use_voice_activity` | Use voice activity detection (vs push-to-talk) |
| `priority_speaker` | Be heard over other speakers in voice channels |

### Message Management

| Permission | Description |
|------------|-------------|
| `manage_messages` | Delete and pin any message across all channels |
| `read_message_history` | View previous messages in channel |

### Messaging

| Permission | Description |
|------------|-------------|
| `send_messages` | Send messages in text channels |
| `send_tts` | Send text-to-speech messages |
| `embed_links` | Embed links in messages |
| `attach_files` | Attach files to messages |
| `add_reactions` | Add reactions to messages |
| `external_emojis` | Use external/custom emojis |

### Invites

| Permission | Description |
|------------|-------------|
| `create_invite` | Create channel invites |
| `manage_invites` | Manage and revoke invites |

### Special

| Permission | Description |
|------------|-------------|
| `mention_everyone` | Mention the @everyone role |
| `use_slash_commands` | Use slash commands in chat |

---

## Default Role Permissions

When a new server is created, the following roles are set up with these permissions:

### Owner
- `administrator` (full access)

### Admin
- `administrator`
- All management permissions
- All moderation permissions
- All voice permissions

### Moderator
- `manage_messages`
- `manage_threads`
- `kick_members`
- `manage_nicknames`
- `mute_members`, `deafen_members`, `move_members`
- `create_invite`
- `use_slash_commands`

### User
- `send_messages`
- `read_message_history`
- `add_reactions`, `attach_files`, `embed_links`, `external_emojis`
- `connect`, `speak`, `stream`, `use_voice_activity`
- `change_nickname`
- `create_invite`
- `use_slash_commands`

---

## Role Hierarchy

Roles have a position value that determines their place in the hierarchy:

1. **Lower position = higher priority** (position 0 is highest)
2. **Users can only manage roles below their highest role**
3. **Protected roles** (`owner`, `admin`) cannot be managed by non-owners

### Example

```
Role: owner     (position: 0) - Can manage all roles
Role: admin     (position: 1) - Can manage moderator, user, and custom roles
Role: moderator (position: 2) - Can manage user and custom roles below them
Role: user      (position: 3) - Cannot manage any roles
Role: bot       (position: 4) - Can be managed by admin and owner
```

---

## Permission Checks

### Checking Permissions in Code

```python
from db import permissions

# Check if user has a permission
if permissions.has_permission(user_id, "manage_roles"):
    # User can manage roles
    pass

# Check with channel context (for deny overrides)
if permissions.has_permission(user_id, "manage_messages", channel_name="general"):
    # User can manage messages in #general
    pass

# Check if user can manage a specific role
can_manage, error = permissions.can_manage_role(actor_id, "moderator")
if not can_manage:
    return error  # "Cannot manage roles at or above your position"

# Check if user can assign a role to another user
can_assign, error = permissions.can_assign_role_to_user(actor_id, target_id, "bot")
if can_assign:
    users.give_role(target_id, "bot")
```

### Using Helper Functions

```python
from handlers.messages.helpers import _require_permission, _require_can_manage_role

# In a handler function
user_id, error = _require_user_id(ws, "Authentication required")
if error:
    return error

error = _require_permission(user_id, "manage_channels", match_cmd)
if error:
    return error  # Returns error response with "Access denied: 'manage_channels' permission required"

error = _require_can_manage_role(user_id, target_role, match_cmd)
if error:
    return error
```

---

## Channel Permission Overrides

Channels can deny specific permissions through their permissions object:

```json
{
  "view": ["user"],
  "send": ["user"],
  "deny": ["manage_messages"]
}
```

In this example, even users with `manage_messages` permission cannot use it in this channel.

---

## Assigning Permissions to Roles

### Via WebSocket Command

```json
{
  "cmd": "role_update",
  "id": "role-uuid-or-name",
  "permissions": ["manage_roles", "kick_members", "use_slash_commands"]
}
```

### Via Database

```python
from db import roles

roles.update_role("bot-role", {
    "permissions": ["manage_roles", "mention_everyone"]
})
```

---

## Special Cases

### Owner Bypass

The `owner` role always passes all permission checks. This cannot be overridden.

### Administrator Permission

Roles with `administrator` permission bypass all checks except:
- Cannot manage the `owner` role
- Cannot modify the server owner's roles

### Protected Roles

The following roles are protected and cannot be deleted:
- `owner`
- `admin`
- `user`

The `owner` and `admin` roles cannot be assigned by users with just `manage_roles` permission.

---

## Bot Users

For bot users (like activity tracking bots), create a dedicated role:

1. Create a role (e.g., "Activity Bot")
2. Assign `manage_roles` permission
3. Set position below admin but above regular users
4. The bot can now assign roles below its position

```json
{
  "cmd": "role_create",
  "name": "Activity Bot",
  "permissions": ["manage_roles"],
  "hoisted": true
}
```

Then assign this role to your bot user, and it can grant activity roles to other users.

---

## API Reference

### `db/permissions.py`

| Function | Description |
|----------|-------------|
| `has_permission(user_id, permission, channel_name=None)` | Check if user has a permission |
| `can_manage_role(actor_id, target_role)` | Check if user can manage a role |
| `can_assign_role_to_user(actor_id, target_user_id, role_name)` | Check if user can assign role to user |
| `role_has_permission(role_name, permission)` | Check if a role has a permission |
| `get_user_roles_sorted(user_id)` | Get user's roles sorted by position |
| `get_highest_role_position(user_id)` | Get user's highest role position |
| `get_all_permissions()` | Get dict of all available permissions |

---

## Migration from Owner-Only

If you're upgrading from the previous owner-only system:

1. **Existing installations**: The owner role already has `administrator` permission
2. **New roles**: Assign appropriate permissions when creating new roles
3. **Custom permissions**: Use `role_update` to add/remove permissions from existing roles
4. **Backward compatible**: Commands that required "owner" role now check for appropriate permissions

---

**See Also:**
- [Roles Data Structure](data/roles.md)
- [Role Commands](commands/role_create.md)
- [Channel Permissions](data/channels.md#permissions)
