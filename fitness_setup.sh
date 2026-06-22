#!/bin/bash
# 减肥计划推送服务 - 安装与自启动设置脚本（给你自己用）
# 与养生计划那套完全独立：不同 LaunchAgent 标签、不同日志，可同时运行
# 运行方式：bash fitness_setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFIER="$SCRIPT_DIR/fitness_notifier.py"
PLIST_LABEL="com.fitness.notifier"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
LOG_PATH="$HOME/Library/Logs/fitness_notifier.log"

echo ""
echo "🔥 减肥计划推送服务安装脚本"
echo "================================"
echo ""

# 1. 检查 Python3
if ! command -v python3 &>/dev/null; then
  echo "❌ 未找到 python3，请先安装 Python3：https://www.python.org/downloads/"
  exit 1
fi
PYTHON3=$(command -v python3)
echo "✅ Python3 路径: $PYTHON3"

# 2. 安装依赖
echo ""
echo "📦 安装 Python 依赖 (requests)..."
$PYTHON3 -m pip install requests --quiet --break-system-packages 2>/dev/null \
  || $PYTHON3 -m pip install requests --quiet
echo "✅ 依赖安装完成"

# 3. 检查 fitness_notifier.py
if [ ! -f "$NOTIFIER" ]; then
  echo "❌ 未找到 fitness_notifier.py，请确保它和本脚本在同一目录"
  exit 1
fi

# 3.5 提醒填 ntfy 主题名
if grep -q '在这里填一个别人猜不到的主题名' "$NOTIFIER"; then
  echo ""
  echo "⚠️  还没填 ntfy 主题名！"
  echo "    打开 fitness_notifier.py，把 NTFY_TOPIC 改成一个别人猜不到的名字，"
  echo "    并在手机 ntfy App 里订阅同名主题，再来运行。"
  echo ""
fi

echo "选择操作："
echo "  1) 现在立即运行推送服务（前台运行）"
echo "  2) 设置为开机自动启动（macOS LaunchAgent）"
echo "  3) 停止并移除自动启动"
echo "  4) 退出"
echo ""
read -rp "请输入选项 [1-4]: " choice

case "$choice" in
  1)
    echo ""
    echo "▶️  启动推送服务（按 Ctrl+C 停止）..."
    echo ""
    $PYTHON3 "$NOTIFIER"
    ;;

  2)
    echo ""
    echo "🔐 配置 pmset 免密权限（让后台进程能定时唤醒 Mac）..."
    SUDOERS_FILE="/etc/sudoers.d/wellness-pmset"
    PMSET_PATH="$(command -v pmset)"
    CURRENT_USER="$(whoami)"
    if [ ! -f "$SUDOERS_FILE" ]; then
      echo "   需要管理员密码授权一次（仅对 pmset 这一个命令生效）"
      echo "${CURRENT_USER} ALL=(root) NOPASSWD: ${PMSET_PATH}" \
        | sudo tee "$SUDOERS_FILE" >/dev/null
      sudo chmod 440 "$SUDOERS_FILE"
      if sudo visudo -cf "$SUDOERS_FILE" >/dev/null 2>&1; then
        echo "✅ pmset 免密权限已配置"
      else
        echo "⚠️  sudoers 校验失败，已回滚"; sudo rm -f "$SUDOERS_FILE"
      fi
    else
      echo "✅ pmset 免密权限已存在（养生计划那套已配过，直接复用）"
    fi

    echo ""
    echo "⚙️  设置 macOS LaunchAgent 开机自启动..."
    mkdir -p "$HOME/Library/LaunchAgents"

    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON3}</string>
        <string>${NOTIFIER}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_PATH}</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"

    echo ""
    echo "✅ 开机自启动已设置！减肥推送服务将在登录后自动运行。"
    echo ""
    echo "   查看运行日志：tail -f $LOG_PATH"
    echo "   手动停止：   launchctl unload $PLIST_PATH"
    echo "   手动启动：   launchctl load $PLIST_PATH"
    ;;

  3)
    echo ""
    if [ -f "$PLIST_PATH" ]; then
      launchctl unload "$PLIST_PATH" 2>/dev/null || true
      rm -f "$PLIST_PATH"
      echo "✅ 已移除减肥计划的开机自启动。"
    else
      echo "ℹ️  未找到自启动配置，可能未设置过。"
    fi
    ;;

  4)
    echo "👋 已退出"
    ;;

  *)
    echo "❌ 无效选项"
    exit 1
    ;;
esac

echo ""
