# Claude Code — Project Instructions

## VPS SSH Access

This project runs on a remote VPS. Use the `ssh-vps` MCP tool to execute commands on it.

### Default user: `claude-user`

All SSH commands must run as **`claude-user`** unless explicitly stated otherwise.

```bash
# Correct — runs as claude-user (the default configured in the MCP server)
ssh-vps: systemctl status agent-news
ssh-vps: docker compose logs --tail=50

# Wrong — do not switch users without permission
ssh-vps: sudo su -
ssh-vps: sudo -i
```

### Root / sudo access

**Never run commands with `sudo` or as `root` without first asking the user for permission.**

Before executing any action that requires elevated privileges, stop and ask:

> "This action requires root/sudo (`<command>`). Do you want me to proceed with elevated privileges?"

Only continue once the user explicitly approves. Examples of actions that require this prompt:
- `sudo <anything>`
- Installing system packages (`apt`, `yum`, etc.)
- Modifying files outside the user's home directory
- Managing system services (`systemctl start/stop/enable`)
- Editing `/etc/...` files
- `docker` commands if the user is not in the docker group

### MCP server setup

The `ssh-vps` MCP server should be configured locally with the `claude-user` account:

```bash
claude mcp add --transport stdio ssh-vps -- npx -y ssh-mcp -- \
  --host=YOUR_VPS_IP \
  --user=claude-user \
  --key=~/.ssh/claude_vps
```

## Project overview

This is a YouTube-news Telegram bot. Key files:
- `agent.py` — main bot logic
- `docker-compose.yml` — container configuration
- `Dockerfile` — container image
- `.env.template` — required environment variables (copy to `.env` on the VPS, never commit `.env`)
- `crontab` — scheduled tasks
