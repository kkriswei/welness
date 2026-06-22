#!/usr/bin/env python3
"""
减肥计划推送脚本（ntfy 版）—— 给你自己用
每天按【你本地时间】发送减肥提醒到你手机，覆盖：饮食/热量、运动、喝水作息、每日称重。

与女朋友那套（养生计划，走 Bark）完全独立：不同服务、不同后台进程，互不干扰。

使用方法：
  1. 手机装 ntfy（App Store / Google Play 搜 "ntfy"），新建订阅，主题名填下方 NTFY_TOPIC
  2. 安装依赖：pip3 install requests
  3. 运行：    python3 fitness_notifier.py
  4. 自启动：  bash fitness_setup.sh  （选 2）

关于主题名（topic）：
  ntfy 不用注册，谁知道主题名谁就能收发。所以请取一个【别人猜不到】的名字，
  例如 chris-fitness-x7k2m9 这种带随机串的。手机 App 里订阅同名主题即可收到。
"""

import time
import requests
import logging
import sys
import subprocess
import datetime

# ===== 配置（只需改这里）=====
NTFY_TOPIC  = "在这里填一个别人猜不到的主题名"   # ← 自己取，手机 ntfy App 订阅同名主题
NTFY_SERVER = "https://ntfy.sh"                  # 官方服务器，免注册；自建服务器改这里
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# 每日推送计划（按【你本地时间】）
# 格式: (时间, 标题, 消息, 优先级1-5)
NOTIFICATIONS = [
    ("07:00", "⚖️ 晨起称重",       "起床、上厕所后、空腹、不穿衣，固定条件称一下，记下数字。看的是【一周趋势】不是单日——水盐波动很正常，别被某天 +0.5kg 吓到。", 3),
    ("07:30", "🍳 高蛋白早餐",     "早餐先吃蛋白质：2个鸡蛋 / 一杯无糖希腊酸奶 / 一份豆制品。蛋白质扛饿、稳血糖，能压住上午想吃零食的冲动，比不吃早餐更不容易暴食。", 4),
    ("09:30", "💧 补水 500ml",     "起来接一大杯水喝掉。很多时候的'饿'其实是渴。喝够水代谢更顺，也能减少不必要的进食。", 3),
    ("10:30", "🧍 久坐起身",       "已经坐很久了。起来走 2 分钟、做几个深蹲或拉伸。NEAT（日常活动消耗）是减脂里被低估的一块，零散动起来积少成多。", 3),
    ("12:00", "🥗 午餐这样配",     "盘子一半蔬菜、四分之一蛋白质、四分之一主食。顺序：先菜和肉，再吃主食。同样的东西换个吃法，血糖更稳、更扛饿、更少囤脂。", 4),
    ("13:00", "🚶 饭后走一走",     "吃完别马上坐下。出去走 10-15 分钟，帮助餐后血糖回落，下午不犯困，顺手又消耗一点。", 3),
    ("15:00", "🍫 下午零食陷阱",   "嘴馋了？先喝杯水等 10 分钟，多半是无聊不是饿。真饿就吃一小把坚果或一个水果，别碰饼干奶茶——一杯奶茶≈半小时跑步。", 3),
    ("16:30", "💧 再补一次水",     "下午再喝 400-500ml。保持补水，避免把口渴误当饥饿，也让晚饭前不至于太饿而点多。", 3),
    ("17:30", "🏃 今天的训练",     "动起来：力量 30 分钟，或有氧/快走 8000 步。力量保肌肉、垫高基础代谢；有氧多烧点热量。哪怕只做 15 分钟，也远胜于零。", 4),
    ("19:00", "🍽️ 晚餐七分饱",     "清淡、七分饱，睡前 3 小时吃完。蛋白质 + 大量蔬菜 + 少量主食。晚上少囤、睡得稳，第二天称重也更友好。", 4),
    ("21:00", "📝 今日复盘打卡",   "花 1 分钟记一下：今天吃得如何、动了没、水喝够没？记录本身就是减脂利器——看得见才控得住。允许不完美，明天继续。", 3),
    ("22:30", "🌙 早点睡",         "睡不够会升高饥饿素、降低代谢，第二天特别想吃高糖高油。现在放下手机，睡够 7 小时，是最轻松的'减肥动作'。晚安。", 3),
]


def send_notify(title: str, body: str, priority: int = 3) -> bool:
    """发送 ntfy 推送通知（JSON 方式，原生支持中文+emoji）"""
    if NTFY_TOPIC.startswith("在这里") or not NTFY_TOPIC:
        log.error("❌ 请先填写 NTFY_TOPIC！在脚本里设置一个别人猜不到的主题名，并在手机 ntfy App 订阅。")
        return False
    try:
        resp = requests.post(
            NTFY_SERVER,
            json={
                "topic":    NTFY_TOPIC,
                "title":    title,
                "message":  body,
                "priority": priority,
            },
            timeout=15,
        )
        resp.raise_for_status()
        log.info(f"✅ 推送成功: {title}")
        return True
    except requests.exceptions.ConnectionError:
        log.warning(f"⚠️  网络连接失败，推送跳过: {title}")
    except requests.exceptions.Timeout:
        log.warning(f"⚠️  请求超时，推送跳过: {title}")
    except Exception as e:
        log.error(f"❌ 推送失败: {title} — {e}")
    return False


# ===== 定时唤醒（让 Mac 在每个提醒前自动醒来）=====
WAKE_LEAD_SECONDS = 90          # 提前多少秒唤醒
CATCH_UP_GRACE_MIN = 60         # 补发窗口（分钟）：到点后这段时间内 Mac 醒来就补发


def _notif_times():
    return sorted(set((int(t[:2]), int(t[3:])) for t, *_ in NOTIFICATIONS))


def next_wake_datetime(now: datetime.datetime) -> datetime.datetime:
    """下一次应唤醒时间 = 下一条提醒(本地时间) - WAKE_LEAD_SECONDS"""
    for h, m in _notif_times():
        notif = now.replace(hour=h, minute=m, second=0, microsecond=0)
        wake = notif - datetime.timedelta(seconds=WAKE_LEAD_SECONDS)
        if wake > now:
            return wake
    h, m = _notif_times()[0]
    notif = (now + datetime.timedelta(days=1)).replace(
        hour=h, minute=m, second=0, microsecond=0)
    return notif - datetime.timedelta(seconds=WAKE_LEAD_SECONDS)


def _pmset(*args, quiet: bool = False) -> bool:
    """非交互调用 pmset（需要 sudoers 免密白名单）"""
    try:
        r = subprocess.run(["sudo", "-n", "pmset", *args],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            if not quiet:
                log.warning(f"⚠️  pmset {' '.join(args)} 失败: {r.stderr.strip()}")
            return False
        return True
    except Exception as e:
        if not quiet:
            log.warning(f"⚠️  pmset 调用异常: {e}")
        return False


_current_wake = None


def sync_wake_schedule():
    """维护下一次唤醒预约（本地时间，pmset 直接用本地时钟）"""
    global _current_wake
    target = next_wake_datetime(datetime.datetime.now())
    stamp = target.strftime("%m/%d/%y %H:%M:%S")
    if stamp == _current_wake:
        return
    if _current_wake:
        _pmset("schedule", "cancel", "wake", _current_wake, quiet=True)
    if _pmset("schedule", "wake", stamp):
        _current_wake = stamp
        log.info(f"⏰ 已预约下一次唤醒: {stamp}")


def due_notifications(now, sent):
    """此刻该补发的提醒：已过点、仍在补发窗口内、今天没发过"""
    grace = datetime.timedelta(minutes=CATCH_UP_GRACE_MIN)
    out = []
    for t, title, msg, prio in NOTIFICATIONS:
        h, m = int(t[:2]), int(t[3:])
        notif = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if t not in sent and notif <= now <= notif + grace:
            out.append((t, title, msg, prio))
    return out


def main():
    log.info("=" * 50)
    log.info("🔥  减肥计划推送服务启动（ntfy）")
    log.info(f"📡  ntfy 服务器: {NTFY_SERVER}")
    log.info(f"📡  ntfy 主题  : {NTFY_TOPIC}")
    log.info(f"🕐  提醒时区  : 本地时间")
    log.info(f"🕐  当前本地时间: {datetime.datetime.now():%Y-%m-%d %H:%M}")
    log.info("=" * 50)
    log.info("已注册每日推送计划（本地时间）：")
    for t, title, *_ in NOTIFICATIONS:
        log.info(f"  📅 {t}  {title}")

    _pmset("schedule", "cancelall")
    sync_wake_schedule()

    log.info("=" * 50)
    log.info("✅  服务运行中，按 Ctrl+C 停止")

    send_notify("🔥 减肥计划已启动",
                f"推送服务运行中！共 {len(NOTIFICATIONS)} 条每日提醒（本地时间）已安排好，开干💪", 4)

    sent_today = set()
    last_date = datetime.datetime.now().date()

    # 启动时跳过超窗口的旧提醒，避免补发一大堆历史提醒
    grace = datetime.timedelta(minutes=CATCH_UP_GRACE_MIN)
    now0 = datetime.datetime.now()
    for t, *_ in NOTIFICATIONS:
        h, m = int(t[:2]), int(t[3:])
        notif = now0.replace(hour=h, minute=m, second=0, microsecond=0)
        if now0 > notif + grace:
            sent_today.add(t)

    try:
        while True:
            now = datetime.datetime.now()
            if now.date() != last_date:
                sent_today.clear()
                last_date = now.date()

            for t, title, msg, prio in due_notifications(now, sent_today):
                if send_notify(title, msg, prio):
                    sent_today.add(t)

            sync_wake_schedule()
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("\n👋  服务已停止")


if __name__ == "__main__":
    main()
