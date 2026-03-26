# Command: self_roles_list

List all self-assignable roles available on the server.

## Request

```json
{
  "cmd": "self_roles_list"
}
```

### Fields

None.

## Response

### On Success

```json
{
  "cmd": "self_roles_list",
  "roles": [
    {
      "name": "gamer",
      "description": "For gaming enthusiasts",
      "color": "#00ff00",
      "assigned": true
    },
    {
      "name": "artist",
      "description": "For artists and creators",
      "color": "#ff00ff",
      "assigned": false
    }
  ]
}
```

## Error Responses

- `{"cmd": "error", "val": "Authentication required"}`

## Notes

- Requires authentication.
- Returns all roles with `self_assignable: true`.
- Each role object includes an `assigned` field indicating whether the authenticated user currently has that role.
- Protected roles (`owner`, `admin`, `moderator`) are never included as they cannot be made self-assignable.

## Role Object Fields

- `name`: The role name.
- `description`: Role description (may be empty string).
- `color`: Role color as hex code (may be `null`).
- `assigned`: Boolean indicating if the user has this role.

## See Also

- [self_role_add](self_role_add.md) - Add a self-assignable role
- [self_role_remove](self_role_remove.md) - Remove a self-assigned role
- [role_create](role_create.md) - Create a role (can set `self_assignable`)
- [role_update](role_update.md) - Update a role's `self_assignable` property
- [roles_list](roles_list.md) - List all roles (owner only)

See implementation: [`handlers/messages/self_role.py`](../../handlers/messages/self_role.py)
