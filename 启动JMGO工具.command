#!/usr/bin/env bash
# JMGO Bonfire OS 工具 — macOS 一键启动器
# 可以放在桌面、下载目录或工具目录内，会自动找到工具本体。
# 端口也会自动识别，不需要手动输入。

set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${HOME:-/Users/wwh}"

TOOL_DIR=""
for candidate in \
    "$SELF_DIR" \
    "$SELF_DIR/jmgo-au-sydney" \
    "$HOME_DIR/Downloads/jmgo-au-sydney" \
    "$HOME_DIR/Downloads" \
; do
    if [ -f "$candidate/bonfire_tuner_full.sh" ]; then
        TOOL_DIR="$candidate"
        break
    fi
done

if [ -z "$TOOL_DIR" ]; then
    echo "[错误] 找不到 bonfire_tuner_full.sh" >&2
    echo "请把工具文件夹 jmgo-au-sydney 放在 ~/Downloads/ 下，或告诉我实际位置。" >&2
    exit 1
fi

IP="${JMGO_DEVICE_IP:-192.168.0.30}"
CONF="$TOOL_DIR/.adb_last_connection"

CACHED_IP=""
CACHED_PORT=""
if [ -f "$CONF" ]; then
    CACHED_IP="$(sed -n 's/^default_ip="\([^"]*\)"$/\1/p' "$CONF" | head -n 1)"
    CACHED_PORT="$(sed -n 's/^default_port="\([0-9]*\)"$/\1/p' "$CONF" | head -n 1)"
fi
[ "$CACHED_IP" = "$IP" ] || CACHED_PORT=""

TARGET="$IP"

# 1) 优先使用 adb 当前已连接的端口（重启后端口会变，这样做最稳）
if command -v adb >/dev/null 2>&1; then
    LIVE="$(adb devices 2>/dev/null | awk -v ip="$IP" '$2 == "device" && index($1, ip ":") == 1 { split($1, a, ":"); print a[2]; exit }')"
    if [ -n "$LIVE" ]; then
        TARGET="$IP:$LIVE"
    fi
fi

# 2) 否则尝试上次成功连接且当前仍可连通的端口
if [ "$TARGET" = "$IP" ] && [ -n "$CACHED_PORT" ] && command -v nc >/dev/null 2>&1; then
    if nc -z -G 1 "$IP" "$CACHED_PORT" >/dev/null 2>&1; then
        TARGET="$IP:$CACHED_PORT"
    fi
fi

echo "正在启动 JMGO Bonfire OS 工具..."
echo "工具目录: $TOOL_DIR"
echo "目标设备: $TARGET"
echo ""
exec "$TOOL_DIR/bonfire_tuner_full.sh" "$TARGET"
