# OriginChats Overview

A high-level introduction to OriginChats concepts and features.

---

## What is OriginChats?

OriginChats is a chat server that lets people communicate in real-time. It supports text messages, voice channels, and custom commands through plugins.

---

## Core Concepts

### Servers

A "server" is your chat community. It has channels, users, and settings. Users connect to your server to chat with each other.

### Channels

Channels are where conversations happen. There are four types:

- **Text Channels** - Send and receive text messages in real-time
- **Voice Channels** - Join to talk with others using voice/audio
- **Forum Channels** - Organized discussions where users create threads for specific topics
- **Separators** - Visual dividers in the channel list (not functional channels)

Channels can have permissions that control who can see them and what users can do.

### Users

Every person in your server is a user. Users have:
- A username
- A status (online, away, etc.)
- Roles that determine their permissions

### Roles & Permissions

Roles control what users can do. Common roles include:
- **Owner** - Full control over the server
- **Moderator** - Can ban users, delete messages
- **Default** - Standard user with basic permissions

Each role has permissions like:
- Viewing channels
- Sending messages
- Editing/deleting messages
- Managing other users

### Messages

Users send messages in text channels. Messages can:
- Contain text (up to a character limit)
- Reply to other messages
- Have reactions (emoji responses)
- Be pinned for importance

### Threads

Threads exist inside forum channels. Users create threads to start new topics, and each thread is a separate conversation.

This helps keep discussions organized - each topic has its own thread instead of mixing everything together.

### Slash Commands

Slash commands are custom actions users can trigger. Examples:
- `/ban @user` - Ban a user (requires permission)
- `/nick newname` - Change your nickname
- `/help` - Show available commands

Server owners can create custom slash commands using plugins.

### Plugins

Plugins add features to your server. They can:
- Respond to messages automatically
- Add new slash commands
- Handle events (user join, message sent, etc.)

---

## How It Works

### Connection Flow

```
User opens client
       ↓
Connects to your server
       ↓
Authenticates with Rotur
       ↓
Receives channels, messages, users
       ↓
Can now send/receive messages
```

### Voice Channels

Voice uses WebRTC (peer-to-peer audio):

```
User joins voice channel
       ↓
Server introduces them to others
       ↓
Users connect directly to each other
       ↓
Audio flows between peers (not through server)
```

This reduces server load and improves voice quality.

### Real-Time Updates

When something happens (message sent, user joins, etc.), the server immediately tells all connected clients. This is how users see new messages instantly.

---

## Features Summary

| Feature | Description |
|---------|-------------|
| Text Messaging | Send, edit, delete, reply, react to messages |
| Voice Channels | Real-time audio with other users |
| User Management | Roles, permissions, bans, timeouts |
| Threads | Organized side discussions |
| Slash Commands | Custom actions triggered by users |
| Plugins | Extend server functionality |
| Rate Limiting | Prevent spam automatically |
| Push Notifications | Notify users even when offline |

---

## Architecture (Simplified)

```
┌─────────────┐
│   Client    │  (Web, desktop, or mobile app)
└──────┬──────┘
       │ WebSocket
       ↓
┌─────────────┐
│   Server    │  (OriginChats)
│  - Routes   │
│  - Handlers │
│  - Plugins  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Database  │  (JSON files)
│  - Users    │
│  - Channels │
│  - Messages │
└─────────────┘
```

**Key Points:**
- Clients connect via WebSocket (persistent connection)
- Server handles all routing and logic
- Data stored in simple JSON files
- Plugins run alongside the server

---

## For Developers

### Building a Client

1. Connect to the WebSocket server
2. Handle the handshake packet
3. Authenticate the user
4. Listen for events (messages, users joining, etc.)
5. Send commands to interact with the server

See: [Client Development Guide](clients.md)

### Creating Plugins

1. Write a Python file with event handlers
2. Place it in the `plugins/` folder
3. Server loads it automatically
4. Plugin can respond to messages, add slash commands, etc.

See: [Plugin Development Guide](plugins.md)

### Available Commands

The server supports many commands for:
- Sending and managing messages
- Creating and managing channels
- Managing users and roles
- Voice channel operations
- Server administration

See: [Command Reference](commands/) (individual files in `docs/commands/`)

---

## Glossary

- **WebSocket** - A persistent connection between client and server
- **WebRTC** - Technology for peer-to-peer audio/video
- **Rotur** - Authentication service used by OriginChats
- **P2P (Peer-to-Peer)** - Direct connection between users (for voice)
- **Rate Limiting** - Preventing users from sending too many messages too quickly
- **Broadcast** - Sending a message to all connected users
- **Handshake** - Initial connection setup between client and server

---

## Next Steps

- **Run your own server:** [Getting Started Guide](getting-started.md)
- **Build a client:** [Client Development](clients.md)
- **Create plugins:** [Plugin Development](plugins.md)
- **Deploy to production:** [Production Guide](production.md)
- **Full API details:** [Command Reference](commands/) (individual files)
