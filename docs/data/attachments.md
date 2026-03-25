# Data Structure: Attachments

Attachments are files uploaded to the server that can be attached to messages. They have configurable expiration times based on user subscription status.

## Attachment Object

```json
{
  "id": "abc123-def456-ghi789",
  "name": "screenshot.png",
  "mime_type": "image/png",
  "size": 12345,
  "url": "https://your-server.com/attachments/abc123-def456-ghi789",
  "expires_at": 1712345678.9,
  "permanent": false
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (UUID) |
| `name` | string | Original file name |
| `mime_type` | string | MIME type of the file |
| `size` | integer | File size in bytes |
| `url` | string | URL to download the attachment |
| `expires_at` | number \| null | Unix timestamp when attachment expires, or null for permanent |
| `permanent` | boolean | Whether the attachment is permanent |

## Storage

Attachments are stored in two locations:

- **Files**: `db/attachments/{attachment_id}.{extension}`
- **Metadata**: `db/attachments.json`

## Deduplication

When uploading, the server calculates a SHA-256 hash of the file content. If an attachment with the same hash already exists:

- The existing attachment is returned instead of creating a duplicate
- The expiration time is reset based on current file size and settings
- The original name is updated to the new upload's filename

This saves storage space and bandwidth when multiple users upload identical files.

## Expiration

### Non-Permanent Attachments

Expiration time is calculated based on file size - smaller files last longer:

| File Size | Expiration |
|-----------|------------|
| ≤ 5 MB | 7 weeks (49 days) |
| 25 MB | 7 days |
| 100 MB | 1 day |

The expiration scales smoothly between these points. For example:
- 10 MB → ~24 days
- 50 MB → ~3 days
- 75 MB → ~2 days

### Permanent Attachments (Rotur Subscribers)

Users with certain Rotur subscription tiers (configurable via `attachments.permanent_tiers`) can upload permanent attachments:

- Permanent attachments expire after `attachments.permanent_expiration_days` days (default: 365 days).
- Default permanent tiers: `pro`, `max`.

## HTTP Access

Attachments can be downloaded via HTTP:

```
GET /attachments/{attachment_id}
```

Returns the file with appropriate `Content-Type` header, or:
- `404` if not found
- `410` if expired

## Rate Limiting

Attachment uploads have separate rate limiting:

- Default: 10 uploads per minute per user.
- Configurable via `attachments.uploads_per_minute`.

## Configuration

See [config.md](../config.md) for all attachment configuration options.

| Config Key | Default | Description |
|------------|---------|-------------|
| `attachments.enabled` | `true` | Enable/disable attachments |
| `attachments.max_size` | `104857600` (100 MB) | Maximum file size in bytes |
| `attachments.permanent_expiration_days` | `365` | Days until permanent attachments expire |
| `attachments.permanent_tiers` | `["pro", "max"]` | Rotur tiers with permanent uploads |
| `attachments.allowed_types` | `["image/*", "video/*", "audio/*", "application/pdf"]` | Allowed MIME types |
| `attachments.uploads_per_minute` | `10` | Upload rate limit |
| `attachments.subscription_cache_ttl` | `300` | Cache time for subscription checks (seconds) |
| `attachments.max_attachments_per_user` | `-1` | Max attachments per user (-1=unlimited, 0=blocked) |

**Note:** Non-permanent attachments have size-based expiration (see table above).
