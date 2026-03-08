# Emoji Object Structure

Custom server emojis are stored as metadata entries keyed by emoji ID.

## Emoji Collection

The server stores emojis as an object where each key is the emoji ID and each value is an emoji object:

```json
{
  "0": {
    "name": "defaultHUH",
    "fileName": "0.svg"
  },
  "1": {
    "name": "wave",
    "fileName": "1.gif"
  }
}
```

## Emoji Object

```json
{
  "name": "defaultHUH",
  "fileName": "0.svg"
}
```

### Fields

- `name`: Custom emoji name. Used for lookup and `:name:` style references.
- `fileName`: Stored image filename inside `db/serverEmojis`.

## Notes

- Emoji IDs are string keys in the collection object.
- Emoji names are unique and case-insensitive for lookup.
- Allowed file types are `gif`, `jpg`, `jpeg`, and `svg`.
- `fileName` is storage metadata, not a public URL.
- Public HTTP access uses `/emojis/{fileName}`.

## Related Commands

- [emoji_add](../commands/emoji_add.md) - Add a custom emoji
- [emoji_update](../commands/emoji_update.md) - Update emoji metadata
- [emoji_delete](../commands/emoji_delete.md) - Delete an emoji
- [emoji_get_all](../commands/emoji_get_all.md) - Return all emoji metadata
- [emoji_get_id](../commands/emoji_get_id.md) - Resolve name to ID
- [emoji_get_filename](../commands/emoji_get_filename.md) - Resolve name to file path

See implementation: [`db/serverEmojis.py`](../../db/serverEmojis.py).
