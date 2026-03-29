# Embed Types

OriginChats supports multiple embed types for rich message content. Embeds can be included in messages via the `embeds` field.

## Overview

Embeds are structured content blocks that can be added to messages. They support:
- Rich text formatting
- Images and thumbnails
- Author and footer sections
- Field-based content
- Polls and interactive content

---

## Embed Types

| Type | Description |
|------|-------------|
| `rich` | Standard embed with full customization (default) |
| `poll` | Interactive poll with voting |
| `link` | URL preview embed |
| `image` | Image-focused embed |
| `video` | Video embed |
| `article` | Article/news embed |

---

## Rich Embed

The default embed type with full customization options.

### Structure

```json
{
  "type": "rich",
  "title": "Embed Title",
  "description": "Embed description text...",
  "url": "https://example.com",
  "color": 16711680,
  "timestamp": "2024-01-01T00:00:00.000Z",
  "author": {
    "name": "Author Name",
    "url": "https://example.com/author",
    "icon_url": "https://example.com/icon.png"
  },
  "thumbnail": {
    "url": "https://example.com/thumb.png"
  },
  "image": {
    "url": "https://example.com/image.png"
  },
  "fields": [
    {
      "name": "Field 1",
      "value": "Field value",
      "inline": true
    }
  ],
  "footer": {
    "text": "Footer text",
    "icon_url": "https://example.com/footer-icon.png"
  }
}
```

### Field Reference

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `type` | string | - | Must be `"rich"` (default) |
| `title` | string | 256 | Embed title |
| `description` | string | 4096 | Main content text |
| `url` | string | - | URL for title link |
| `color` | integer | - | Decimal color (0-16777215) |
| `timestamp` | string | - | ISO 8601 timestamp |

### Author Object

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `name` | string | 256 | Author display name |
| `url` | string | - | Author link |
| `icon_url` | string | - | Author icon URL |

### Footer Object

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `text` | string | 2048 | Footer text |
| `icon_url` | string | - | Footer icon URL |

### Image/Thumbnail Object

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Image URL |
| `width` | integer | Image width (optional) |
| `height` | integer | Image height (optional) |

### Field Object

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `name` | string | 256 | Field title |
| `value` | string | 1024 | Field content |
| `inline` | boolean | - | Display inline (default: false) |

---

## Poll Embed

Interactive polls with voting functionality.

### Structure

```json
{
  "type": "poll",
  "title": "Poll Question",
  "poll": {
    "question": "What's your favorite color?",
    "options": [
      {"id": "red", "text": "Red", "emoji": "🔴"},
      {"id": "blue", "text": "Blue", "emoji": "🔵"},
      {"id": "green", "text": "Green", "emoji": "🟢"}
    ],
    "allow_multiselect": false,
    "expires_at": 1704067200
  }
}
```

### Poll Object

| Field | Type | Max | Description |
|-------|------|-----|-------------|
| `question` | string | 300 | Poll question |
| `options` | array | 10 | Array of 2-10 options |
| `allow_multiselect` | boolean | - | Allow multiple votes |
| `expires_at` | number | - | Unix timestamp for expiration |

### Poll Option Object

| Field | Type | Max | Description |
|-------|------|-----|-------------|
| `id` | string | 50 | Unique option ID |
| `text` | string | 100 | Option display text |
| `emoji` | string | - | Optional emoji |

See [Polls Documentation](polls.md) for full details.

---

## Link Embed

URL preview embeds, typically auto-generated from links.

### Structure

```json
{
  "type": "link",
  "url": "https://example.com/article",
  "title": "Page Title",
  "description": "Page description from meta tags",
  "thumbnail": {
    "url": "https://example.com/og-image.png"
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Must be `"link"` |
| `url` | string | The linked URL |

---

## Image Embed

Image-focused embed for displaying images prominently.

### Structure

```json
{
  "type": "image",
  "title": "Image Title",
  "description": "Image caption",
  "image": {
    "url": "https://example.com/photo.png",
    "width": 1920,
    "height": 1080
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Must be `"image"` |
| `image` | object | Must include `url` |

---

## Video Embed

Video embed for displaying video content.

### Structure

```json
{
  "type": "video",
  "title": "Video Title",
  "description": "Video description",
  "url": "https://example.com/video.mp4",
  "thumbnail": {
    "url": "https://example.com/video-thumb.png"
  }
}
```

---

## Article Embed

Article/news embed for long-form content.

### Structure

```json
{
  "type": "article",
  "title": "Article Title",
  "description": "Article summary or excerpt...",
  "url": "https://example.com/article",
  "author": {
    "name": "Author Name"
  },
  "timestamp": "2024-01-01T00:00:00.000Z",
  "thumbnail": {
    "url": "https://example.com/article-image.png"
  },
  "footer": {
    "text": "Publication Name"
  }
}
```

---

## Global Limits

| Limit | Value |
|-------|-------|
| Embeds per message | 10 |
| Fields per embed | 25 |
| Total characters per embed | 6000 |

The 6000 character limit includes:
- Title
- Description
- Field names and values
- Author name
- Footer text
- Poll question and options

---

## Using Embeds in Messages

### With `message_new`

```json
{
  "cmd": "message_new",
  "channel": "general",
  "content": "Check out this embed!",
  "embeds": [
    {
      "title": "Example Embed",
      "description": "This is a rich embed example",
      "color": 5814333,
      "fields": [
        {"name": "Field 1", "value": "Value 1", "inline": true},
        {"name": "Field 2", "value": "Value 2", "inline": true}
      ]
    }
  ]
}
```

### With `message_edit`

```json
{
  "cmd": "message_edit",
  "channel": "general",
  "id": "message-id",
  "embeds": [
    {
      "title": "Updated Embed",
      "description": "New description"
    }
  ]
}
```

---

## Color Reference

Colors are decimal integers from 0 to 16777215 (0xFFFFFF).

| Color | Decimal | Hex |
|-------|---------|-----|
| Red | 16711680 | #FF0000 |
| Green | 65280 | #00FF00 |
| Blue | 255 | #0000FF |
| Yellow | 16776960 | #FFFF00 |
| Purple | 9109759 | #8B008B |
| Cyan | 65535 | #00FFFF |
| White | 16777215 | #FFFFFF |
| Black | 0 | #000000 |

---

## Validation

All embeds are validated before being saved:

1. **Type validation**: Must be a valid embed type
2. **Character limits**: All fields respect max lengths
3. **Total character count**: Embeds under 6000 chars
4. **Required fields**: Type-specific required fields present
5. **Field counts**: Within limits (embeds: 10, fields: 25)

Invalid embeds will return an error:
```json
{
  "cmd": "error",
  "val": "Embed 0: Embed title cannot exceed 256 characters"
}
```

---

## Examples

### Notification Embed

```json
{
  "title": "🔔 New Notification",
  "description": "You have a new message!",
  "color": 3447003,
  "timestamp": "2024-01-15T12:00:00.000Z",
  "footer": {"text": "OriginChats"}
}
```

### Error Embed

```json
{
  "title": "❌ Error",
  "description": "Something went wrong",
  "color": 15548997,
  "fields": [
    {"name": "Error Code", "value": "ERR_001", "inline": true},
    {"name": "Details", "value": "Invalid parameter", "inline": true}
  ]
}
```

### Success Embed

```json
{
  "title": "✅ Success",
  "description": "Your changes have been saved",
  "color": 5763719,
  "footer": {"text": "Settings updated at 12:00 PM"}
}
```

### Stats Embed

```json
{
  "title": "📊 Server Statistics",
  "color": 5814333,
  "fields": [
    {"name": "Members", "value": "1,234", "inline": true},
    {"name": "Messages", "value": "56,789", "inline": true},
    {"name": "Channels", "value": "42", "inline": true}
  ]
}
```

---

**See Also:**
- [Messages](commands/message_new.md)
- [Polls](polls.md)
- [Webhooks](webhooks.md)
