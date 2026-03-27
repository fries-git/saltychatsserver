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
      "description": "Owns the server so has all the perms fr",
      "color": "#FF00FF"
    },
    "admin": {
      "description": "Administrator role with full permissions.",
      "color": "#FF0000"
    },
    "gamer": {
      "description": "For gaming enthusiasts",
      "color": "#00ff00",
      "self_assignable": true
    }
  }
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`
- `{"cmd": "error", "val": "Access denied: owner role required"}`

## Notes

- Returns all roles as a dictionary keyed by role name.
- Each role object contains:
  - `description`: Role description (optional)
  - `color`: Hex color code (optional)
  - `self_assignable`: Boolean indicating if the role is self-assignable

## See Also

- [role_create](role_create.md) - Create a new role
- [role_update](role_update.md) - Update an existing role
- [role_delete](role_delete.md) - Delete a role

See implementation: [`handlers/message.py`](../../handlers/message.py) (search for `case "roles_list":`).
