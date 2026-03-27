# Configuration: config.json

This file contains the main configuration for the OriginChats server. Below is a description of each section and field:

---

## limits

- **post_content**: *(int)*
  - Maximum number of characters allowed in a single message/post.
- **search_results**: *(int)*
  - Maximum number of results returned by `messages_search`.

## uploads

- **emoji_allowed_file_types**: *(list of str)*
  - Allowed file extensions for custom emoji uploads.

## attachments

- **enabled**: *(bool)*
  - Whether the attachment system is enabled.
- **max_size**: *(int)*
  - Maximum file size for attachments in bytes. Default: 104857600 (100 MB).
- **permanent_expiration_days**: *(int)*
  - Number of days before permanent attachments expire. Default: 365.
- **permanent_tiers**: *(list of str)*
  - Rotur subscription tiers that can upload permanent attachments. Default: ["pro", "max"].
  - Valid tiers: "lite", "plus", "drive", "pro", "max".
- **allowed_types**: *(list of str)*
  - Allowed MIME types for uploads. Supports wildcards (e.g., "image/*"). Default: ["image/*", "video/*", "audio/*", "application/pdf"].
- **uploads_per_minute**: *(int)*
  - Rate limit for attachment uploads per user. Default: 10.
- **subscription_cache_ttl**: *(int)*
  - Cache duration for Rotur subscription status checks in seconds. Default: 300.
- **max_attachments_per_user**: *(int)*
  - Maximum number of attachments a user can have at once. Default: -1 (unlimited).
  - `-1`: Unlimited (only limited by expiration)
  - `0`: Block all uploads
  - `> 0`: Delete oldest attachment when limit reached

### Expiration by File Size

Non-permanent attachments have expiration times based on file size:

| File Size | Expiration |
|-----------|------------|
| ≤ 5 MB | 7 weeks (49 days) |
| 25 MB | 7 days |
| 100 MB | 1 day |

The expiration time scales smoothly between these points - smaller files last longer.

## rate_limiting

- **enabled**: *(bool)*
  - Whether rate limiting is enabled for message sending.
- **messages_per_minute**: *(int)*
  - Maximum number of messages a user can send per minute.
- **burst_limit**: *(int)*
  - Maximum number of messages allowed in a short burst before cooldown is enforced.
- **cooldown_seconds**: *(int)*
  - Number of seconds a user must wait after hitting the burst limit.

## DB

- **channels**: *(str)*
  - Path to the channels database file.
- **users**: *(object)*
  - **file**: *(str)*
    - Path to the users database file.
  - **default**: *(object)*
    - **roles**: *(list of str)*
      - Default roles assigned to new users.

## websocket

- **host**: *(str)*
  - Host address for the websocket server.
- **port**: *(int)*
  - Port number for the websocket server.

## service

- **name**: *(str)*
  - Name of the service.
- **version**: *(str)*
  - Version of the service.

## server

- **name**: *(str)*
  - Name of the server instance.
- **owner**: *(object)*
  - **name**: *(str)*
    - Name of the server owner.
- **icon**: *(str)*
  - URL to the server icon image, or the filename of a file already stored in `db/serverAssets`; it will be exposed as `/server-assets/icon`.
- **banner**: *(str)*
  - URL to the server banner image, or the filename of a file already stored in `db/serverAssets`; it will be exposed as `/server-assets/banner`.
- **url**: *(str)*
  - Public base URL of the server, used to build hosted links for local server icon and banner files.

---

## Adding New Config

When adding a new config value, follow these 3 steps:

1. Add the default value in `config_builder.py` under `DEFAULT_CONFIG`.
2. If it should be set during setup, add a prompt in `setup.py` and add the parsed value to the overrides passed into `build_config(...)`.
3. Read it in runtime code through `get_config_value(...)` from `config_store.py`, or through the local `_config_value(...)` helper in handlers when `server_data["config"]` is already available.

Example:

- Add `limits.search_results` in `config_builder.py`.
- Prompt for it in `setup.py`.
- Read it with `get_config_value("limits", "search_results", default=30)`.

---

**Location:** `config.json`

This file should be kept secure, especially fields containing API keys or sensitive URLs.
