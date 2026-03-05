#!/bin/bash
# External gateway health check - tests WebSocket connection like a real user

GATEWAY_URL="wss://chuday.eu"
GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN}"

echo "🔍 Testing OpenClaw Gateway (external user perspective)"
echo "URL: $GATEWAY_URL"
echo ""

# Test 1: HTTPS accessibility
echo "Test 1: HTTPS endpoint..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://chuday.eu/clawagent/ --max-time 10)
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ HTTPS OK (status: $HTTP_STATUS)"
else
    echo "❌ HTTPS FAILED (status: $HTTP_STATUS)"
    exit 1
fi

# Test 2: WebSocket connection (with token)
echo ""
echo "Test 2: WebSocket connection..."

# Create a simple WebSocket test
WSCAT_OUTPUT=$(timeout 5 websocat -n1 "$GATEWAY_URL" 2>&1 || echo "CONNECTION_FAILED")

if echo "$WSCAT_OUTPUT" | grep -q "unauthorized\|too many\|rate"; then
    echo "❌ WebSocket FAILED: Rate limited or unauthorized"
    echo "   Error: $WSCAT_OUTPUT"
    exit 1
elif echo "$WSCAT_OUTPUT" | grep -q "CONNECTION_FAILED"; then
    echo "❌ WebSocket FAILED: Cannot connect"
    exit 1
else
    echo "✅ WebSocket reachable"
fi

# Test 3: Check if services are running
echo ""
echo "Test 3: Gateway processes..."
GATEWAY_PROCS=$(ps aux | grep "openclaw-gateway.*18789" | grep -v grep | wc -l)
if [ "$GATEWAY_PROCS" -gt 0 ]; then
    echo "✅ Gateway running ($GATEWAY_PROCS processes)"
else
    echo "❌ Gateway NOT running"
    exit 1
fi

echo ""
echo "✅ All external health checks passed"
