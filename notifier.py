#!/usr/bin/env python3
"""
养生计划推送脚本（Bark 版，国内 iPhone 可用）
每天按时发送养生提醒到女朋友手机

使用方法：
  1. 安装依赖：pip3 install schedule requests
  2. 填写下方 BARK_KEY（从 Bark App 里复制）
  3. 运行：    python3 notifier.py
  4. 自启动：  bash setup.sh

Bark 获取方式：
  iPhone → App Store 搜索「Bark」→ 安装 → 打开 App
  → 首页显示一个 URL，复制最后那串字符就是你的 KEY
  例：https://api.day.app/AbCdEf123456/ → KEY 是 AbCdEf123456
"""

import schedule
import time
import requests
import logging
import sys

# ===== 配置（只需改这里）=====
BARK_KEY = "bsiHn9WBb64ki6ymjMgZXm"   # Bark Key
# ==============================

BARK_SERVER = "https://api.day.app"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# 每日推送计划
# 格式: (时间, 标题, 消息, 优先级, tags)
NOTIFICATIONS = [
    ("07:30", "☀️ 早安，起床啦～",   "先别看手机！床头那杯水喝掉，600ml，喝完再刷。空腹喝温水能启动肠胃、排毒、控油，比任何护肤品都便宜。今天也是皮肤变好的一天💧",                                                              "default", "seedling"),
    ("07:45", "🥐 出门前吃点东西",   "不吃早餐→血糖崩→午饭暴食→下午犯困→皮肤变差，这个链条你经历过多少次了？楼下便利店：茶叶蛋1个+三明治，5分钟搞定，今天的代谢从这里开始。",                                                  "high",    "bread"),
    ("08:30", "🚶 提前一站下车！",   "现在就准备下车，走路去公司。15分钟步行=今天的运动量完成✅ 不用健身房，不用额外时间。走路时挺胸收腹，练姿势的同时顺便燃脂，一举两得。",                                                      "high",    "walking"),
    ("10:30", "💧 离开座位30秒",     "已经坐了2小时了。站起来，走到茶水间，接600ml水喝掉。顺手做个肩颈绕圈，左右各5次。久坐会让血液循环变差，直接影响脸色——起来动一下，比涂口红还提气色。",                                    "default", "droplet"),
    ("12:00", "🥗 午饭时间，吃聪明点", "外卖备注写上：少油少辣，多加蔬菜。选择顺序：蒸菜>炒菜>油炸。深色蔬菜（菠菜/西兰花/胡萝卜）含抗氧化成分，直接护肤。今天蔬菜达标了，皮肤会悄悄记账的🌿",                               "default", "salad"),
    ("12:30", "🚶 饭后不要坐着",     "吃完饭立刻坐着=血糖飙升+消化变慢+下午犯困。出去走10分钟，哪怕就在楼道里转，也能让血糖稳住、消化提速。走完回来，下午精力比同事强一截。",                                                    "default", "walking"),
    ("14:30", "🍵 下午补水时间",     "现在感觉有点困？不是因为累，是因为缺水。喝400ml水或无糖绿茶（绿茶里的EGCG是护肤成分，比很多精华便宜100倍）。奶茶今天先放放，给皮肤一个机会🍃",                                            "default", "tea"),
    ("16:30", "🧍 肩颈快要断了吧",   "对着屏幕盯了一下午，现在做：双手交叉放脑后，头缓缓向后仰，停5秒。然后左耳贴左肩、右耳贴右肩，各停5秒。就这几个动作，预防颈椎病，顺便让下班后不那么疲惫。",                                "default", "person_standing"),
    ("18:30", "🏃 下班了！再走一段", "提前一站下车，走路回家。今天上班路走过了，现在这段是加成——两段加起来30分钟，正好达到每日运动量。走路时深呼吸，把白天的压力呼出去，到家时整个人会轻松很多。",                             "high",    "runner"),
    ("19:30", "🍜 晚饭吃轻一点",     "今天辣的吃够了吗？晚上试试：砂锅粥+小菜，或者蒸菜套餐，或者清汤面。清淡的晚饭让肠胃休息，睡眠质量提升，明天早上起来脸不浮肿。你会发现皮肤状态和前一天晚饭直接挂钩🌾",               "default", "noodles"),
    ("21:00", "✨ 护肤3步，今天做了吗", "第1步：温水洗脸（35度，别用热水）→ 第2步：爽肤水轻拍到吸收 → 第3步：保湿乳锁水。总共5分钟。坚持30天会有人问你用了什么产品✨",                                                           "default", "sparkles"),
    ("22:30", "🌙 该放下手机了",     "皮肤在23:00-02:00修复最活跃，这是真的。今天喝水了、走路了、护肤了——已经比昨天的自己好了一点点。放下手机，给自己10分钟缓冲，晚安🌙",                                                        "default", "crescent_moon"),
]


def send_bark(title: str, body: str, sound: str = "birdsong") -> bool:
    """发送 Bark 推送通知（国内 iPhone 可用）"""
    if BARK_KEY == "在这里粘贴Bark的Key":
        log.error("❌ 请先填写 BARK_KEY！打开 Bark App 复制你的 Key 填到脚本里。")
        return False
    try:
        resp = requests.post(
            f"{BARK_SERVER}/push",
            json={
                "title":      title,
                "body":       body,
                "device_key": BARK_KEY,
                "group":      "养生计划",
                "sound":      sound,
                "badge":      1,
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


def setup_schedule():
    """注册所有每日推送任务"""
    for t, title, msg, priority, tags in NOTIFICATIONS:
        def make_job(title=title, msg=msg):
            def job():
                send_bark(title, msg)
            return job
        schedule.every().day.at(t).do(make_job())
        log.info(f"  📅 {t}  {title}")


def main():
    log.info("=" * 50)
    log.info("🌱  养生计划推送服务启动")
    log.info(f"📲  Bark Key  : {BARK_KEY[:6]}***")
    log.info(f"🖥   Bark 服务器: {BARK_SERVER}")
    log.info("=" * 50)
    log.info("已注册每日推送计划：")

    setup_schedule()

    log.info("=" * 50)
    log.info("✅  服务运行中，按 Ctrl+C 停止")

    # 启动时发送一条确认推送
    send_bark(
        "🌱 养生计划已启动",
        f"推送服务运行中！共 {len(NOTIFICATIONS)} 条每日提醒已安排好，加油💪",
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("\n👋  服务已停止")


if __name__ == "__main__":
    main()
