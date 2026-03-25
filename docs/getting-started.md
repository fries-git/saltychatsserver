# Getting Started

How to connect to and interact with an OriginChats server.

---

## Connection Basics

OriginChats uses WebSocket for real-time communication. Your client connects once and keeps the connection open to send and receive messages instantly.

### Connection URL

```
ws://your-server:5613
```

Replace `your-server` with the server's address and `5613` with the configured port.

---

## Connection Flow

Here's what happens when a user connects:

```
1. Connect to WebSocket
      ↓
2. Receive handshake packet
      ↓
3. Authenticate user
      ↓
4. Receive "ready" packet
      ↓
5. Connected! Can now send/receive commands
```

---

## Step 1: Handshake

When you connect, the server immediately sends a handshake packet:

```json
{
  "cmd": "handshake",
  "val": {
    "server": {
      "name": "My Server",
      "icon": "https://...",
      "banner": "https://..."
    },
    "limits": {
      "post_content": 2000
    },
    "version": "1.1.0",
    "validator_key": "originChats-abc123",
    "capabilities": ["message_new", "message_edit", ...]
  }
}
```

**What to do:**
- Display server info (name, icon, banner) to the user
- Save the `validator_key` - you'll need it for authentication
- `capabilities` lists all supported commands (optional, for feature detection)

---

## Step 2: Authentication

OriginChats uses Rotur for authentication. The flow is:

1. User logs in at `https://rotur.dev/auth?return_to=YOUR_APP`
2. User is redirected back with a token in the url like ?token=
3. Generate a short-lived validator from the token
4. Send the validator to the chat server

### Generate a Validator

Call the Rotur API to exchange your token for a validator:

```javascript
// Use the validator_key from the handshake
const response = await fetch(
  `https://api.rotur.dev/generate_validator?auth=${token}&key=${validatorKey}`
);
const data = await response.json();
const validator = data.validator;
```

**Key points:**
- Your raw auth token is ONLY sent to `api.rotur.dev` (never to other services)
- Validators are short-lived and safe to pass to chat servers
- Each service (like OriginChats) has its own `validator_key`

### Send Authentication

Send the validator to the chat server:

```json
{
  "cmd": "auth",
  "validator": "validator-token-here"
}
```

### Authentication Response

**Success:**
```json
{
  "cmd": "auth_success",
  "val": "Authentication successful"
}
```

Then immediately receive:
```json
{
  "cmd": "ready",
  "user": {
    "username": "alice",
    "roles": ["user", "moderator"],
    "id": "USR:12345..."
  },
  "validator": "optional-user-validator"
}
```

The `validator` field is optional - the server may return a validator token for the user.

**Failure:**
```json
{
  "cmd": "auth_error",
  "val": "Invalid validator token"
}
```

---

## Step 3: Ready State

After authentication succeeds, you can:

- Request channels with `channels_get`
- Request messages with `messages_get`
- List users with `users_list`
- Send messages with `message_new`
- Join voice channels with `voice_join`

---

## Sending Commands

All commands follow the same format:

```json
{
  "cmd": "command_name",
  "param1": "value1",
  "param2": "value2"
}
```

### Example: Send a Message

```json
{
  "cmd": "message_new",
  "channel": "general",
  "content": "Hello, world!"
}
```

### Example: Get Channels

```json
{
  "cmd": "channels_get"
}
```

---

## Receiving Events

The server broadcasts events to all connected clients. You don't need to request them - just listen.

### New Message

```json
{
  "cmd": "message_new",
  "message": {
    "id": "msg-uuid",
    "user": "alice",
    "content": "Hello!",
    "timestamp": 1234567890.123,
    "type": "message",
    "pinned": false
  },
  "channel": "general",
  "global": true
}
```

When `"global": true`, broadcast to all users who can see that channel.

### User Joined (First Time)

```json
{
  "cmd": "user_join",
  "user": {
    "username": "bob",
    "roles": ["user"],
    "color": "#00aaff"
  }
}
```

### User Connected (Any Session)

```json
{
  "cmd": "user_connect",
  "user": {
    "username": "bob",
    "roles": ["user"],
    "color": "#00aaff"
  }
}
```

### User Left

```json
{
  "cmd": "user_disconnect",
  "username": "bob"
}
```

---

## Keep-Alive

The server sends periodic ping packets:

```json
{ "cmd": "ping" }
```

You don't need to respond. Just keep the connection open.

---

## Error Handling

Errors are simple:

```json
{
  "cmd": "error",
  "val": "Error message here",
  "src": "message_new"
}
```

- `val` - Human-readable error message
- `src` - The command that caused the error (optional)

Common errors:
- `"User not authenticated"` - Need to login first
- `"Unknown command: xyz"` - Command doesn't exist
- `"Access denied to this channel"` - No permission
- `"Rate limited"` - Sending too fast

---

## Rate Limiting

If a user sends messages too quickly:

```json
{
  "cmd": "rate_limit",
  "length": 5000
}
```

- `length` - How long to wait (milliseconds)
- Wait before sending more messages
- Show user a "slow down" indicator

---

## Message Format

All messages use JSON. Keep these in mind:

- Message content has a max length (check `limits.post_content` from handshake)
- Messages can reply to other messages (`reply_to` field)
- Messages can have reactions (emoji + users who reacted)
- Messages can be pinned

---

## Voice Channels

Voice uses WebRTC for peer-to-peer audio.

### Joining Voice

1. Send `voice_join` with channel name and your `peer_id`
2. Server responds with list of participants
3. Connect directly to other users' `peer_id` using WebRTC
4. Audio flows between peers, not through server

### Voice Events

**User joined:**
```json
{
  "cmd": "voice_user_joined",
  "channel": "voice-general",
  "user": {
    "id": "USR:123",
    "username": "alice",
    "peer_id": "webrtc-peer-id",
    "muted": false
  },
  "global": true
}
```

**User left:**
```json
{
  "cmd": "voice_user_left",
  "channel": "voice-general",
  "username": "alice",
  "global": true
}
```

**User muted/unmuted:**
```json
{
  "cmd": "voice_user_updated",
  "channel": "voice-general",
  "user": {
    "id": "USR:123",
    "username": "alice",
    "muted": true
  },
  "global": true
}
```

---

## Complete Example

Here's a minimal connection flow:

```javascript
// 1. Connect
const ws = new WebSocket('ws://localhost:5613');

// 2. Handle handshake
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.cmd === 'handshake') {
    console.log('Connected to:', data.val.server.name);
    // Save validator_key for auth
    const validatorKey = data.val.validator_key;
    
    // 3. Authenticate (after getting token from Rotur)
    ws.send(JSON.stringify({
      cmd: 'auth',
      validator: getUserValidatorToken()
    }));
  }
  
  if (data.cmd === 'auth_success') {
    console.log('Logged in!');
  }
  
  if (data.cmd === 'ready') {
    console.log('User:', data.user.username);
    // 4. Request channels
    ws.send(JSON.stringify({ cmd: 'channels_get' }));
  }
  
  if (data.cmd === 'channels_get') {
    console.log('Channels:', data.channels);
  }
  
  if (data.cmd === 'message_new') {
    console.log('New message:', data.message.content);
    // Display message in UI
  }
  
  if (data.cmd === 'error') {
    console.error('Error:', data.val);
  }
};
```

---

## What's Next?

- **All commands:** See [Command Reference](commands/) (individual files)
- **Data structures:** See [Reference](reference.md)
- **Building a client:** See [Client Development](clients.md)
- **Server setup:** See main [README](../README.md)

---

## Quick Reference

| Action | Command | Key Fields |
|--------|---------|------------|
| Send message | `message_new` | `channel`, `content` |
| Get messages | `messages_get` | `channel` |
| Edit message | `message_edit` | `id`, `channel`, `content` |
| Delete message | `message_delete` | `id`, `channel` |
| Get channels | `channels_get` | - |
| Join voice | `voice_join` | `channel`, `peer_id` |
| Leave voice | `voice_leave` | - |
| Set status | `status_set` | `status` |
| Typing indicator | `typing` | `channel` |
