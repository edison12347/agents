#!/bin/bash
# Migrate OpenClaw from system services to user services

set -e

echo "🔄 Migrating OpenClaw to user services..."
echo ""

# Step 1: Stop system services
echo "Step 1: Stopping system services..."
sudo systemctl stop openclaw-builder openclaw-aivar openclaw-lina
sudo systemctl disable openclaw-builder openclaw-aivar openclaw-lina
echo "✅ System services stopped and disabled"
echo ""

# Step 2: Enable lingering (services start at boot without login)
echo "Step 2: Enabling lingering for claude-user..."
sudo loginctl enable-linger claude-user
echo "✅ Lingering enabled"
echo ""

# Step 3: Reload user systemd daemon
echo "Step 3: Reloading user systemd daemon..."
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user daemon-reload
echo "✅ User systemd reloaded"
echo ""

# Step 4: Enable and start user services
echo "Step 4: Enabling and starting user services..."
systemctl --user enable openclaw-builder openclaw-aivar openclaw-lina
systemctl --user start openclaw-builder openclaw-aivar openclaw-lina
echo "✅ User services started"
echo ""

# Step 5: Check status
echo "Step 5: Checking status..."
sleep 3
systemctl --user status openclaw-builder openclaw-aivar openclaw-lina --no-pager | grep -E "Active:|Main PID:"
echo ""

echo "✅ Migration complete!"
echo ""
echo "From now on, use these commands:"
echo "  systemctl --user status openclaw-builder"
echo "  systemctl --user restart openclaw-aivar"
echo "  systemctl --user stop openclaw-lina"
echo ""
echo "No sudo needed! 🎉"
