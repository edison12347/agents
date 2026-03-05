# Migrating OpenClaw to User Services

## What This Does

Moves OpenClaw services from system services (require sudo) to user services (no sudo needed).

**Before:**
```bash
sudo systemctl restart openclaw-builder  # Requires sudo
```

**After:**
```bash
systemctl --user restart openclaw-builder  # No sudo!
```

## Migration Steps

**Run the migration script:**
```bash
/home/builder/scripts/migrate-to-user-services.sh
```

**Or manually:**
```bash
# 1. Stop and disable system services
sudo systemctl stop openclaw-builder openclaw-aivar openclaw-lina
sudo systemctl disable openclaw-builder openclaw-aivar openclaw-lina

# 2. Enable lingering (services start at boot)
sudo loginctl enable-linger claude-user

# 3. Start user services
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user daemon-reload
systemctl --user enable openclaw-builder openclaw-aivar openclaw-lina
systemctl --user start openclaw-builder openclaw-aivar openclaw-lina

# 4. Verify
systemctl --user status openclaw-builder openclaw-aivar openclaw-lina
```

## New Commands

**Status:**
```bash
systemctl --user status openclaw-builder
systemctl --user status openclaw-aivar
systemctl --user status openclaw-lina
```

**Restart:**
```bash
systemctl --user restart openclaw-builder
systemctl --user restart openclaw-aivar
systemctl --user restart openclaw-lina
```

**Logs:**
```bash
journalctl --user -u openclaw-builder -f
```

**List all:**
```bash
systemctl --user list-units "openclaw-*"
```

## Benefits

✅ **No sudo needed** - Builder can restart services directly  
✅ **Better security** - User-level isolation  
✅ **Cleaner permissions** - No privilege escalation  
✅ **Same functionality** - Everything works exactly the same  

## What Changed

**Service files moved:**
- From: `/etc/systemd/system/openclaw-*.service`
- To: `~/.config/systemd/user/openclaw-*.service`

**Key differences:**
- Removed `User=claude-user` (services run as current user)
- Changed `WantedBy=multi-user.target` → `WantedBy=default.target`
- Everything else identical

## Healthcheck Updates

After migration, healthcheck script can restart services without sudo:
```bash
systemctl --user restart openclaw-builder  # Works!
```

## Rollback (if needed)

```bash
# Stop user services
systemctl --user stop openclaw-builder openclaw-aivar openclaw-lina
systemctl --user disable openclaw-builder openclaw-aivar openclaw-lina

# Start system services
sudo systemctl enable openclaw-builder openclaw-aivar openclaw-lina
sudo systemctl start openclaw-builder openclaw-aivar openclaw-lina
```

## Status

- ✅ User service files created
- ⏳ Waiting for migration script to run
- ⏳ System services still active (need to stop)
- ⏳ User services not started yet

**Ready to migrate:** Run `/home/builder/scripts/migrate-to-user-services.sh`
