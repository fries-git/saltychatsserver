# Command: roles_list

List all roles on the server.

## Request

```json
{
  "cmd": "roles_list"
}
```

### Fields

None.

## Response

### On Success

```json
{
  "cmd": "roles_list",
  "roles": {
    "owner": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "owner",
      "description": "Owns the server so has all the perms fr",
      "color": "#FF00FF",
      "hoisted": true,
      "self_assignable": false,
      "category": null,
      "position": 0
    },
    "admin": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "admin",
      "description": "Administrator role with full permissions.",
      "color": "#FF0000",
      "hoisted": true,
      "self_assignable": false,
      "category": null,
      "position": 1
    },
    "gamer": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "gamer",
      "description": "For gaming enthusiasts",
      "color": "#00ff00",
      "hoisted": false,
      "self_assignable": true,
      "category": "interests",
      "position": 5
    }
  }
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`

## Notes

- Returns all roles as a dictionary keyed by role name.
- Roles are ordered by `position` (set via `role_reorder`).
- Each role object contains:
  - `id`: Unique identifier for the role (UUID)
  - `name`: Role name
  - `description`: Role description (optional)
  - `color`: Hex color code (optional)
  - `hoisted`: Boolean indicating if displayed separately in user list
  - `self_assignable`: Boolean indicating if users can self-assign
  - `category`: Category for grouping (optional)
  - `position`: Sort order position
- Use the `id` field for role updates/deletes to allow renaming.

## See Also

- [role_create](role_create.md) - Create a new role
- [role_update](role_update.md) - Update an existing role
- [role_delete](role_delete.md) - Delete a role
- [role_reorder](role_reorder.md) - Reorder roles

See implementation: [`handlers/messages/role.py`](../../handlers/messages/role.py).
