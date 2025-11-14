# -*- coding: utf-8 -*-
import asyncio
import random
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
import re
import ast
from typing import Dict, Any, List
from telethon import TelegramClient, events, errors
from telethon.tl import functions, types
from pyrogram import Client, filters, errors as pyro_errors

# ==================== تنظیمات Telethon ====================
api_id = 282992
api_hash = "Api id"
session_name = "Im"

client = TelegramClient(session_name, api_id, api_hash)

# ==================== تنظیمات Pyrogram ====================
SESSION_NAME = "selfbot_session"
DATA_PATH = Path("selfbot_data.json")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ==================== داده‌های مشترک ====================
DATA_DIR = "data_self"
os.makedirs(DATA_DIR, exist_ok=True)

features_file = os.path.join(DATA_DIR, "features.json")
love_file = os.path.join(DATA_DIR, "love.json")
enemies_file = os.path.join(DATA_DIR, "enemies.json")
admins_file = os.path.join(DATA_DIR, "admins.json")
friends_file = os.path.join(DATA_DIR, "friends.json")
insults_file = os.path.join(DATA_DIR, "insults.json")
group_file = os.path.join(DATA_DIR, "group.json")

# داده‌های Pyrogram
default_data = {
    "keywords": [],
    "clock": False,
    "font": "ساده",
    "schedules": [],
    "panel_text": ""
}
pyro_data: Dict[str, Any] = default_data.copy()

_save_lock = asyncio.Lock()

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره‌سازی {path}: {e}")

def load_pyro_data():
    global pyro_data
    if DATA_PATH.exists():
        try:
            with DATA_PATH.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    pyro_data = {**default_data, **loaded}
                else:
                    pyro_data = default_data.copy()
        except Exception as e:
            print(f"Error loading pyro data: {e}")
            pyro_data = default_data.copy()
    else:
        pyro_data = default_data.copy()

async def save_pyro_data():
    async with _save_lock:
        try:
            with DATA_PATH.open("w", encoding="utf-8") as f:
                json.dump(pyro_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving pyro data: {e}")

# بارگذاری داده‌ها
features = load_json(features_file, {
    "clock": True, "qa": True, "bold": True, "hashtag": True,
    "fortune": True, "funny": True, "calc": True, "minigame": True, "love": True,
    "love_chance": 30, "love_max": 1, "enemy": True, "enemy_chance": 50, "enemy_max": 3,
    "friend": True, "friend_chance": 40, "friend_max": 1, "group_manage": True,
    "auto_bold": False
})
love_targets = load_json(love_file, {})
enemies_list = load_json(enemies_file, {})
admins_list = load_json(admins_file, {})
friends_list = load_json(friends_file, {})
insults = load_json(insults_file, [])
main_group = load_json(group_file, None)

load_pyro_data()

# اگر فحش‌ها خالی هستند، فحش‌های پیش‌فرض را اضافه کن
if not insults:
    insults = [
        "کسننت مادرجنده", "خارکسه ننه خرابی", "کیری ناموس", "کسمادر سکسننه",
        "خارکونی کوسمادر", "خعارکونی سکسناموس", "ننه کس صادراتی", "کسنانوست بشه",
        "کسننه خارکسه", "کسخارت بکل مادرکسه", "کسننت مردی؟", "غیبی خارکس",
        "خارکسه کونی", "ننه جنده", "مادرت چند؟", "کسننت خارکسه", "ای مادرتو گاییدم",
        "کیر تو خارت", "ننه چاکر کیر", "کیر خر مادرجنده"
    ]
    save_json(insults_file, insults)

def save_state():
    save_json(features_file, features)
    save_json(love_file, love_targets)
    save_json(enemies_file, enemies_list)
    save_json(admins_file, admins_list)
    save_json(friends_file, friends_list)
    save_json(insults_file, insults)
    save_json(group_file, main_group)

# ==================== فونت‌ها برای Pyrogram ====================
FONT_STYLES = {
    "ساده": "0123456789",
    "ضخیم": "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "نازک": "0123456789",
    "ریاضی": "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "دوبل": "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"
}

def convert_digits(text: str, font_key: str) -> str:
    if font_key not in FONT_STYLES:
        return text
    base = "0123456789"
    font = FONT_STYLES[font_key]
    trans = str.maketrans(base, font)
    return text.translate(trans)

# ==================== پنل Telethon ====================
def get_panel():
    status = lambda x: "✅" if x else "❌"
    panel_text = (
        "⚙️ پنل ربات :\n\n"
        "1) ساعت ⏰: {clock}\n"
        "2) سوال و جواب ❓: {qa}\n"
        "3) متن ضخیم 🖋: {bold}\n"
        "4) هشتگ 🏷️: {hashtag}\n"
        "5) فال 🔮: {fortune}\n"
        "6) جوک 😂: {funny}\n"
        "7) ماشین‌حساب 🧮: {calc}\n"
        "8) مینی‌گیم 🕹️: {minigame}\n"
        "9) عشق ❤️: {love}\n"
        "10) احتمال ابراز 💌: {love_chance}%\n"
        "11) حداکثر پیام 💝: {love_max}\n"
        "12) دشمن 👿: {enemy}\n"
        "13) احتمال حمله ⚔️: {enemy_chance}%\n"
        "14) حداکثر حمله 🔥: {enemy_max}\n"
        "15) رفاقت 🤝: {friend}\n"
        "16) احتمال رفاقت 🌟: {friend_chance}%\n"
        "17) حداکثر پیام 🤗: {friend_max}\n"
        "18) فحش‌ها 📂: {insults_count} عدد\n"
        "19) مدیریت گروه 👥: {group_manage}\n"
        "20) گروه اصلی 🏠: {group_id}\n"
        "21) حالت ضخیم خودکار 🔤: {auto_bold}"
    )
    return panel_text.format(
        clock=status(features.get("clock", True)),
        qa=status(features.get("qa", True)),
        bold=status(features.get("bold", True)),
        hashtag=status(features.get("hashtag", True)),
        fortune=status(features.get("fortune", True)),
        funny=status(features.get("funny", True)),
        calc=status(features.get("calc", True)),
        minigame=status(features.get("minigame", True)),
        love=status(features.get("love", True)),
        love_chance=features.get("love_chance",30),
        love_max=features.get("love_max",1),
        enemy=status(features.get("enemy", True)),
        enemy_chance=features.get("enemy_chance",50),
        enemy_max=features.get("enemy_max",3),
        friend=status(features.get("friend", True)),
        friend_chance=features.get("friend_chance",40),
        friend_max=features.get("friend_max",1),
        insults_count=len(insults),
        group_manage=status(features.get("group_manage", True)),
        group_id=main_group if main_group else "❌ تنظیم نشده",
        auto_bold=status(features.get("auto_bold", False))
    )

# ==================== پنل Pyrogram ====================
def get_pyro_panel(me):
    lines = [
        "╔═════════════════════════",
        "║ 🛠️ پنل مدیریت سِلف‌بات Pyrogram",
        f"║ 👤 کاربر: {me.first_name or ''} @{me.username or ''}",
        f"║ 🆔 آیدی: {me.id}",
        "╠═════════════════════════",
        f"║ 🕒 ساعت: {'فعال' if pyro_data.get('clock') else 'غیرفعال'}",
        f"║ 🔤 فونت ساعت: {pyro_data.get('font')}",
        f"║ 😈 تعداد دشمن‌ها: {len(pyro_data.get('enemies', []))}",
        f"║ 🔔 تعداد کلمات کلیدی: {len(pyro_data.get('keywords', []))}",
        f"║ 📥 دانلودها در پوشه: {DOWNLOAD_DIR.resolve()}",
        "╚═════════════════════════",
        "",
        "دستورات Pyrogram (فارسی):",
        "- پنل پی -> نمایش این متن",
        "- ذخیره پی -> ذخیره دستی تنظیمات",
        "- افزودن کلمه <کلمه>",
        "- حذف کلمه <کلمه>",
        "- لیست کلمه‌ها",
        "- پاک کردن کلمه‌ها",
        "- فعال کردن ساعت / غیرفعال کردن ساعت",
        "- فونت ساعت <ساده|ضخیم|نازک|ریاضی|دوبل>",
        "- دانلود پی (دانلود ۵۰ پیام اخیر از چت)",
        "- پاک کردن دانلودها",
        "- تنظیم نام <نام جدید>",
        "- تنظیم بیو <متن بیو>",
        "- تنظیم عکس (ریپلای به عکس با متن 'تنظیم عکس')",
        "- زمانبندی YYYY-MM-DDTHH:MM:SS | متن",
        "- لیست زمانبندی",
        "- حذف زمانبندی <id>",
        ""
    ]
    if pyro_data.get("panel_text"):
        lines.append("نکته: " + pyro_data["panel_text"])
    return "\n".join(lines)

OWNER_ID = None
MASTER_ID = 29403984

def is_admin(user_id):
    return user_id==OWNER_ID or user_id==MASTER_ID or str(user_id) in admins_list

def is_owner(user_id):
    return user_id==OWNER_ID or user_id==MASTER_ID

def is_main_group(chat_id):
    return main_group and chat_id == main_group

# ==================== داده‌های Telethon ====================
love_replies = [
    "عاشقتم ❤️", "فداتشم 🌹", "دورت بگردم 🥰", "جیگرمی 😘", "نفسمی 💕",
    "نوکرتم 🙏", "زندگیمی 💖", "قلبم فقط برای تو می‌پته 💓", "میذاری 💝",
    "فداتشم؟ 😘", "اخه فداتشم 😍", "اخه قربونت برم 🥰", "نازنینم 🌹",
    "خوشگلم 💖", "قند نباتم 🍬"
]

jokes=["چرا کامپیوتر بیمار شد؟ چون ویروس گرفت! 😄"]
fortunes=["امروز روز خوبی است! 🌟"]
quotes=["زندگی همان چیزی است که برایت اتفاق می‌افتد وقتی برنامه‌ریزی می‌کنی."]

friend_replies = [
    "داداشمی", "حاجی پشمتم", "عشقی", "برارمی", "ستونی", "بشینیم؟", "داشمی"
]

welcome_messages = [
    "خوش اومدی عزیزم {name} 🌹",
    "اهلا و سهلا {name} به جمع ما خوش اومدی 💫",
    "سلام {name} عزیز، خوشحالیم که بهمون پیوستی 🥰",
    "وای چه خبر! {name} اومده 😍 خوش اومدی عشقم",
    "به به به {name} جان، منتظرت بودیم 🤩"
]

# ==================== فونت زیبا برای ساعت ====================
def get_fancy_time():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    fancy_numbers = {
        '0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④',
        '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨'
    }
    time_str = f"{hour:02d}:{minute:02d}"
    fancy_time = ''.join(fancy_numbers.get(char, char) for char in time_str)
    return fancy_time

# ==================== محاسبه ایمن با ast ====================
def safe_eval(expr):
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
        ast.UAdd, ast.USub, ast.Load, ast.Tuple, ast.Call
    )

    expr = expr.replace('×','*').replace('÷','/').replace('^','**').replace('،',',')
    if re.search(r"[a-zA-Z_@\$]", expr):
        raise ValueError("عبارت مجاز نیست")

    node = ast.parse(expr, mode='eval')
    for n in ast.walk(node):
        if not isinstance(n, allowed_nodes):
            raise ValueError("عبارت شامل گره غیرمجاز است")

    compiled = compile(node, "<string>", "eval")
    return eval(compiled, {"__builtins__": {}} , {})

# ==================== بررسی ادمین گروه ====================
async def is_group_administrator(event):
    try:
        if not event.is_group:
            return False
        participant = await event.client.get_permissions(event.chat_id, event.sender_id)
        return getattr(participant, "is_admin", False)
    except Exception:
        return False

# ==================== هندلر پیام‌های Telethon ====================
@client.on(events.NewMessage)
async def telethon_handler(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    text = (event.raw_text or "").strip()
    if not text:
        return

    # حالت ضخیم خودکار (برای ادمین‌ها)
    if features.get("auto_bold", False) and is_admin(user_id) and not text.startswith(('/', 'پنل', 'ضخیم', 'هشتگ', 'فال', 'جوک', 'نقل قول')):
        try:
            await event.edit(f"**{text}**")
            return
        except Exception:
            pass

    in_main_group = is_main_group(chat_id)
    is_group_admin = await is_group_administrator(event)

    # ابراز علاقه خودکار
    if str(user_id) in love_targets and features.get("love", True):
        chance = features.get("love_chance", 30)
        max_msgs = features.get("love_max", 1)
        if random.randint(1,100) <= chance and love_replies:
            for _ in range(max_msgs):
                await event.reply(random.choice(love_replies))
                await asyncio.sleep(0.3)

    # حمله به دشمنان
    if str(user_id) in enemies_list and features.get("enemy", True) and insults:
        chance = features.get("enemy_chance", 50)
        max_msgs = features.get("enemy_max", 3)
        if random.randint(1,100) <= chance:
            for _ in range(random.randint(1, max_msgs)):
                await event.reply(random.choice(insults))
                await asyncio.sleep(0.3)

    # پیام‌های رفاقت
    if str(user_id) in friends_list and features.get("friend", True):
        chance = features.get("friend_chance", 40)
        max_msgs = features.get("friend_max", 1)
        if random.randint(1,100) <= chance and friend_replies:
            for _ in range(max_msgs):
                await event.reply(random.choice(friend_replies))
                await asyncio.sleep(0.3)

    # دستورات مدیریت و پنل - فقط برای ادمین‌ها
    if not is_admin(user_id):
        # قابلیت‌های عمومی
        if features.get("qa") and text.endswith("؟"):
            await event.reply(random.choice(["بله","خیر","شاید"]))
            return
        if features.get("fortune") and text == "فال":
            await event.reply(random.choice(fortunes))
            return
        if features.get("funny") and text == "جوک":
            await event.reply(random.choice(jokes))
            return
        if features.get("qa") and text == "نقل قول":
            await event.reply(random.choice(quotes))
            return
        if features.get("hashtag") and text.startswith("هشتگ "):
            msg = text[6:].strip()
            if msg:
                hashtags = " ".join(f"#{w}" for w in msg.split())
                try:
                    await event.edit(hashtags)
                except Exception:
                    await event.reply(hashtags)
            return
        if features.get("bold") and text.startswith("ضخیم ") and not features.get("auto_bold", False):
            msg = text[6:].strip()
            if msg:
                try:
                    await event.edit(f"**{msg}**")
                except Exception:
                    await event.reply(f"**{msg}**")
            return
        if features.get("calc") and (text.startswith("= ") or text.startswith("محاسبه ")):
            expr = text.split(" ",1)[1] if " " in text else ""
            if not expr and text.startswith("= "):
                expr = text[2:]
            if expr:
                try:
                    res = safe_eval(expr)
                    await event.reply(f"نتیجه: {res}")
                except Exception:
                    await event.reply("❌ محاسبه نامعتبر است")
            return
        return

    # دستورات ادمین‌ها
    if text in ["پنل","/panel"]:
        await event.reply(get_panel())
        return

    if text == "/setgroup" and event.is_group:
        if is_owner(user_id):
            main_group = chat_id
            save_json(group_file, main_group)
            await event.reply(f"✅ گروه اصلی تنظیم شد!\nآیدی: {main_group}")
        else:
            await event.reply("❌ فقط مالک ربات می‌تواند گروه اصلی را تنظیم کند")
        return

    if text == "/delgroup" and is_owner(user_id):
        main_group = None
        save_json(group_file, main_group)
        await event.reply("✅ گروه اصلی حذف شد!")
        return

    if text.isdigit():
        feature_map = {
            1: "clock", 2: "qa", 3: "bold", 4: "hashtag", 5: "fortune",
            6: "funny", 7: "calc", 8: "minigame", 9: "love",
            12: "enemy", 15: "friend", 19: "group_manage", 21: "auto_bold"
        }
        num = int(text)
        if num in feature_map:
            features[feature_map[num]] = not features.get(feature_map[num], False)
            save_state()
            await event.reply(f"ویژگی {num} ({feature_map[num]}) {'✅ فعال' if features[feature_map[num]] else '❌ غیرفعال'}")
        elif num in [10,11,13,14,16,17]:
            await event.reply("📝 برای تغییر این مقدار از دستور مربوطه استفاده کنید")
        return

    # مدیریت فحش‌ها
    if text.startswith("/addinsult"):
        parts = text.split(" ",1)
        if len(parts) < 2 or not parts[1].strip():
            await event.reply("❌ فرمت: /addinsult <متن>")
            return
        insults.append(parts[1].strip())
        save_json(insults_file, insults)
        await event.reply(f"✅ فحش اضافه شد. مجموع: {len(insults)}")
        return

    if text.startswith("/delinsult"):
        parts = text.split(" ",1)
        if len(parts) < 2:
            await event.reply("❌ فرمت: /delinsult <شماره>")
            return
        try:
            idx = int(parts[1]) - 1
            if 0 <= idx < len(insults):
                removed = insults.pop(idx)
                save_json(insults_file, insults)
                await event.reply(f"✅ حذف شد: {removed}")
            else:
                await event.reply("❌ شماره نامعتبر است")
        except Exception:
            await event.reply("❌ عدد معتبر نیست")
        return

    if text == "/insults":
        if insults:
            msg = "\n".join([f"{i+1}. {w}" for i,w in enumerate(insults[:50])])
            if len(insults) > 50:
                msg += f"\n... و {len(insults)-50} فحش دیگر"
            await event.reply("📂 لیست فحش‌ها:\n" + msg)
        else:
            await event.reply("❌ هیچ فحشی ثبت نشده است")
        return

    # اسپم امن
    if text.startswith("/b "):
        parts = text.split(" ",2)
        if len(parts) < 3:
            await event.reply("❌ فرمت: /b <تعداد> <متن> (حداکثر 5 پیام)")
            return
        try:
            count = int(parts[1])
            if count > 5: count = 5
            for _ in range(count):
                await event.reply(parts[2])
                await asyncio.sleep(0.7)
        except Exception:
            await event.reply("❌ تعداد باید عدد باشد")
        return

    # مدیریت ادمین‌ها
    if text.startswith("/setadmin"):
        if is_owner(user_id):
            uid = None
            if event.is_reply:
                uid = (await event.get_reply_message()).sender_id
            else:
                parts = text.split(" ",1)
                if len(parts) < 2:
                    await event.reply("❌ فرمت: ریپلای + /setadmin یا /setadmin <آیدی>")
                    return
                try:
                    uid = int(parts[1])
                except:
                    uid = parts[1]
            if uid:
                admins_list[str(uid)] = True
                save_json(admins_file, admins_list)
                await event.reply(f"✅ کاربر {uid} به لیست ادمین‌ها اضافه شد!")
        else:
            await event.reply("❌ فقط مالک ربات می‌تواند ادمین اضافه کند")
        return

    if text.startswith("/deladmin"):
        if is_owner(user_id):
            uid = None
            if event.is_reply:
                uid = (await event.get_reply_message()).sender_id
            else:
                parts = text.split(" ",1)
                if len(parts) < 2:
                    await event.reply("❌ فرمت: ریپلای + /deladmin یا /deladmin <آیدی>")
                    return
                try:
                    uid = int(parts[1])
                except:
                    uid = parts[1]
            if str(uid) in admins_list:
                del admins_list[str(uid)]
                save_json(admins_file, admins_list)
                await event.reply(f"✅ کاربر {uid} از لیست ادمین‌ها حذف شد!")
            else:
                await event.reply("❌ این کاربر در لیست ادمین‌ها نیست")
        else:
            await event.reply("❌ فقط مالک ربات می‌تواند ادمین حذف کند")
        return

    if text == "/admins":
        if admins_list:
            admin_list_text = "👥 لیست ادمین‌ها:\n"
            for i,(admin_id,_) in enumerate(admins_list.items(),1):
                admin_list_text += f"{i}. آیدی: {admin_id}\n"
            await event.reply(admin_list_text)
        else:
            await event.reply("❌ هیچ ادمینی اضافه نشده است")
        return

    # تغییر پارامترها
    if text.startswith("/setparam "):
        parts = text.split(" ",2)
        if len(parts) < 3:
            await event.reply("❌ فرمت: /setparam <name> <value>")
            return
        name = parts[1].strip()
        value = parts[2].strip()
        if name in ["love_chance","enemy_chance","friend_chance","love_max","enemy_max","friend_max"]:
            try:
                val = int(value)
                features[name] = val
                save_state()
                await event.reply(f"✅ مقدار {name} روی {val} تنظیم شد")
            except:
                await event.reply("❌ مقدار باید عدد باشد")
        else:
            await event.reply("❌ نام پارامتر قابل تنظیم نیست")
        return

    # اضافه/حذف عشق، دشمن، دوست
    for cmd, target_list, file_name in [
        ("/setlove", love_targets, love_file),
        ("/dellove", love_targets, love_file),
        ("/setenemy", enemies_list, enemies_file),
        ("/delenemy", enemies_list, enemies_file),
        ("/setfriend", friends_list, friends_file),
        ("/delfriend", friends_list, friends_file)
    ]:
        if text.startswith(cmd):
            uid = None
            if event.is_reply:
                uid = (await event.get_reply_message()).sender_id
            else:
                parts = text.split(" ",1)
                if len(parts) < 2:
                    await event.reply(f"❌ فرمت: ریپلای + {cmd} یا {cmd} <آیدی>")
                    return
                try: uid = int(parts[1])
                except: uid = parts[1]
            
            if cmd.startswith("/set"):
                if uid:
                    target_list[str(uid)] = True
                    save_json(file_name, target_list)
                    await event.reply(f"✅ کاربر {uid} به لیست {'عشق' if 'love' in cmd else 'دشمن' if 'enemy' in cmd else 'دوستان'} اضافه شد")
            else:  # del commands
                if str(uid) in target_list:
                    del target_list[str(uid)]
                    save_json(file_name, target_list)
                    await event.reply(f"✅ کاربر {uid} از لیست {'عشق' if 'love' in cmd else 'دشمن' if 'enemy' in cmd else 'دوستان'} حذف شد")
                else:
                    await event.reply("❌ این کاربر در لیست نیست")
            return

    # دستورات مدیریتی گروه
    if in_main_group and features.get("group_manage", True) and is_group_admin and is_admin(user_id):
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            user_id_to_manage = reply_msg.sender_id
            
            if text.startswith("/ban"):
                try:
                    await event.client.edit_permissions(chat_id, user_id_to_manage, view_messages=False)
                    await event.reply("✅ کاربر بن شد!")
                except Exception:
                    await event.reply("❌ خطا در بن کردن کاربر")
                return
            elif text.startswith("/unban"):
                try:
                    await event.client.edit_permissions(chat_id, user_id_to_manage, view_messages=True)
                    await event.reply("✅ کاربر آنبن شد!")
                except Exception:
                    await event.reply("❌ خطا در آنبن کردن کاربر")
                return
            elif text.startswith("/mute"):
                try:
                    await event.client.edit_permissions(chat_id, user_id_to_manage, send_messages=False)
                    await event.reply("✅ کاربر سایلنت شد!")
                except Exception:
                    await event.reply("❌ خطا در سایلنت کردن کاربر")
                return
            elif text.startswith("/unmute"):
                try:
                    await event.client.edit_permissions(chat_id, user_id_to_manage, send_messages=True)
                    await event.reply("✅ کاربر آنسایلنت شد!")
                except Exception:
                    await event.reply("❌ خطا در آنسایلنت کردن کاربر")
                return
            elif text.startswith("/pin"):
                try:
                    await reply_msg.pin()
                    await event.reply("✅ پیام پین شد!")
                except Exception:
                    await event.reply("❌ خطا در پین کردن پیام")
                return
            elif text.startswith("/kick"):
                try:
                    await event.client.kick_participant(chat_id, user_id_to_manage)
                    await event.reply("✅ کاربر اخراج شد!")
                except Exception:
                    await event.reply("❌ خطا در اخراج کاربر")
                return

# ==================== خوشامدگویی Telethon ====================
@client.on(events.ChatAction)
async def welcome_new_member(event):
    try:
        if features.get("group_manage", True) and is_main_group(event.chat_id):
            if event.user_joined or event.user_added:
                user = event.user or (await event.get_user())
                name = getattr(user, "first_name", "کاربر")
                welcome = random.choice(welcome_messages).format(name=name)
                await event.reply(welcome)
    except Exception:
        pass

# ==================== ساعت زنده Telethon ====================
async def update_telethon_clock():
    while True:
        if features.get("clock", False):
            try:
                fancy_time = get_fancy_time()
                await client(functions.account.UpdateProfileRequest(
                    last_name=fancy_time
                ))
            except Exception:
                pass
        await asyncio.sleep(60)

# ==================== Pyrogram Client ====================
pyro_app = Client(SESSION_NAME, api_id=api_id, api_hash=api_hash)

# ==================== Flood Protect ====================
def flood_protect(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (errors.FloodWait, pyro_errors.FloodWait) as e:
            wait = e.value
            print(f"FloodWait: منتظر {wait} ثانیه می‌شم...")
            await asyncio.sleep(wait)
            return await func(*args, **kwargs)
    return wrapper

# ==================== وظایف پس‌زمینه Pyrogram ====================
async def update_pyro_clock():
    """هر ۶۰ ثانیه بیو رو آپدیت می‌کنه اگر فعال باشه"""
    while True:
        try:
            if pyro_data.get("clock"):
                now = datetime.now().strftime("%H:%M")
                styled = convert_digits(now, pyro_data.get("font", "ساده"))
                try:
                    await pyro_app.update_profile(bio=f"🕒 {styled}")
                    print(f"Pyro Clock updated -> {styled}")
                except pyro_errors.FloodWait as e:
                    print(f"Pyro Clock floodwait {e.value}s")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"Pyro Clock update error: {e}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Pyro Clock task exception: {e}")
            await asyncio.sleep(10)

async def schedule_runner():
    """هر ۳۰ ثانیه چک می‌کنه آیا پیام زمانبندی‌شده داریم"""
    while True:
        try:
            now_ts = datetime.now(timezone.utc).timestamp()
            changed = False
            for schedule in pyro_data.get("schedules", []):
                if schedule.get("done"):
                    continue
                try:
                    target_ts = datetime.fromisoformat(schedule["ts_iso"]).replace(tzinfo=timezone.utc).timestamp()
                except Exception:
                    schedule["done"] = True
                    changed = True
                    continue
                if target_ts <= now_ts:
                    chat = schedule.get("chat_id", "me")
                    text = schedule.get("text", "")
                    try:
                        if chat == "me":
                            await pyro_app.send_message("me", text)
                        else:
                            await pyro_app.send_message(chat, text)
                        print(f"Pyro Scheduled sent to {chat}: {text[:40]}...")
                        schedule["done"] = True
                        changed = True
                    except Exception as e:
                        print(f"Pyro Error sending scheduled msg: {e}")
                        await asyncio.sleep(2)
            if changed:
                await save_pyro_data()
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Pyro Schedule runner exception: {e}")
            await asyncio.sleep(10)

# ==================== هندلر دستورات Pyrogram ====================
@pyro_app.on_message(filters.me & filters.text)
@flood_protect
async def pyro_command_handler(client, message):
    """دستورات فارسی برای کنترل سلف‌بات Pyrogram"""
    text = (message.text or "").strip()
    lower = text.lower()

    # پنل متنی
    if lower == "پنل پی":
        try:
            me = await client.get_me()
            panel = get_pyro_panel(me)
            return await message.reply(panel)
        except Exception as e:
            return await message.reply(f"خطا در گرفتن پنل: {e}")

    # ذخیره دستی
    if lower == "ذخیره پی":
        await save_pyro_data()
        return await message.reply("✅ اطلاعات Pyrogram ذخیره شد.")

    # افزودن کلمه
    if lower.startswith("افزودن کلمه"):
        arg = text.replace("افزودن کلمه", "", 1).strip()
        if arg:
            if arg not in pyro_data["keywords"]:
                pyro_data["keywords"].append(arg)
                await save_pyro_data()
                return await message.reply(f"✅ کلمه '{arg}' اضافه شد.")
            else:
                return await message.reply("⚠️ این کلمه قبلاً وجود دارد.")
        return await message.reply("روش: `افزودن کلمه <کلمه>`")

    # حذف کلمه
    if lower.startswith("حذف کلمه"):
        arg = text.replace("حذف کلمه", "", 1).strip()
        if arg in pyro_data["keywords"]:
            pyro_data["keywords"].remove(arg)
            await save_pyro_data()
            return await message.reply(f"✅ کلمه '{arg}' حذف شد.")
        return await message.reply("🚫 این کلمه در لیست نیست.")

    # لیست کلمه‌ها
    if lower == "لیست کلمه‌ها":
        kws = pyro_data.get("keywords", [])
        if not kws:
            return await message.reply("لیست کلمات کلیدی خالی است.")
        return await message.reply("📚 کلمات کلیدی:\n" + "\n".join(kws))

    # پاک کردن کلمه‌ها
    if lower == "پاک کردن کلمه‌ها":
        pyro_data["keywords"].clear()
        await save_pyro_data()
        return await message.reply("🧹 همه کلمات کلیدی پاک شدند.")

    # فعال/غیرفعال کردن ساعت در بیو
    if lower == "فعال کردن ساعت":
        pyro_data["clock"] = True
        await save_pyro_data()
        return await message.reply("✅ ساعت فعال شد (بیو هر دقیقه آپدیت می‌شود).")

    if lower == "غیرفعال کردن ساعت":
        pyro_data["clock"] = False
        await save_pyro_data()
        return await message.reply("🛑 ساعت غیرفعال شد.")

    # تغییر فونت ساعت
    if lower.startswith("فونت ساعت"):
        arg = text.replace("فونت ساعت", "", 1).strip()
        if arg in FONT_STYLES:
            pyro_data["font"] = arg
            await save_pyro_data()
            return await message.reply(f"🔤 فونت ساعت به '{arg}' تغییر کرد.")
        else:
            return await message.reply("فونت نامعتبر است. فونت‌ها: " + ", ".join(FONT_STYLES.keys()))

    # دانلود  (50 پیام اخیر)
    if lower == "دانلود پی":
        await message.reply("⏳ دانلود رسانه‌ها در حال انجام است (تا ۵۰ پیام اخیر)...")
        count = 0
        try:
            async for m in client.get_chat_history(message.chat.id, limit=50):
                if m.media:
                    try:
                        path = await client.download_media(m, file_name=str(DOWNLOAD_DIR / f"{m.id}"))
                        count += 1
                    except Exception as e:
                        print(f"Pyro Download error for {m.id}: {e}")
            return await message.reply(f"✅ دانلود تمام شد. تعداد فایل‌ها: {count}")
        except Exception as e:
            return await message.reply(f"خطا در دانلود: {e}")

    if lower == "پاک کردن دانلودها":
        removed = 0
        for f in DOWNLOAD_DIR.iterdir():
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
        return await message.reply(f"🧹 {removed} فایل حذف شد.")

    # تنظیم نام کاربری
    if lower.startswith("تنظیم نام"):
        arg = text.replace("تنظیم نام", "", 1).strip()
        if not arg:
            return await message.reply("روش: `تنظیم نام <نام جدید>`")
        try:
            await client.update_profile(first_name=arg)
            return await message.reply(f"✅ نام به '{arg}' تغییر کرد.")
        except Exception as e:
            return await message.reply(f"خطا در تنظیم نام: {e}")

    # تنظیم بیو
    if lower.startswith("تنظیم بیو"):
        arg = text.replace("تنظیم بیو", "", 1).strip()
        if not arg:
            return await message.reply("روش: `تنظیم بیو <متن بیو>`")
        try:
            await client.update_profile(bio=arg)
            return await message.reply("✅ بیو تغییر کرد.")
        except Exception as e:
            return await message.reply(f"خطا در تنظیم بیو: {e}")

    # تنظیم عکس پروفایل
    if lower == "تنظیم عکس":
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("⚠️ برای تنظیم عکس، باید به یک عکس ریپلای کنی و متن 'تنظیم عکس' رو بفرستی.")
        try:
            file = await client.download_media(message.reply_to_message, file_name=str(DOWNLOAD_DIR / f"profile_{message.reply_to_message.id}.jpg"))
            await client.set_profile_photo(photo=file)
            return await message.reply("✅ عکس پروفایل آپدیت شد.")
        except Exception as e:
            return await message.reply(f"خطا در تنظیم عکس: {e}")

    # زمانبندی ارسال پیام
    if lower.startswith("زمانبندی"):
        parts = text.split("|", 1)
        if len(parts) < 2:
            return await message.reply("روش: زمانبندی YYYY-MM-DDTHH:MM:SS | متن پیام\nمثال: زمانبندی 2025-12-01T13:45:00 | سلام")
        time_part = parts[0].replace("زمانبندی", "", 1).strip()
        msg_part = parts[1].strip()
        try:
            ts = datetime.fromisoformat(time_part)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            iso = ts.isoformat()
            sid = f"{int(datetime.now().timestamp())}_{len(pyro_data['schedules'])}"
            pyro_data["schedules"].append({"id": sid, "ts_iso": iso, "chat_id": "me", "text": msg_part, "done": False})
            await save_pyro_data()
            return await message.reply(f"⏱️ پیام زمانبندی شد: id={sid}")
        except Exception as e:
            return await message.reply(f"فرمت زمان نامعتبر یا خطا: {e}")

    if lower == "لیست زمانبندی":
        schedules = pyro_data.get("schedules", [])
        if not schedules:
            return await message.reply("هیچ زمانبندی‌ای وجود ندارد.")
        lines = ["🗓️ زمانبندی‌ها:"]
        for s in schedules:
            lines.append(f"id:{s['id']} | {s['ts_iso']} | sent:{s.get('done', False)} | text:{s['text'][:40]}")
        return await message.reply("\n".join(lines))

    if lower.startswith("حذف زمانبندی"):
        arg = text.replace("حذف زمانبندی", "", 1).strip()
        if not arg:
            return await message.reply("روش: حذف زمانبندی <id>")
        schedules = pyro_data.get("schedules", [])
        new_schedules = [s for s in schedules if s.get("id") != arg]
        if len(new_schedules) == len(schedules):
            return await message.reply("شناسه زمانبندی پیدا نشد.")
        pyro_data["schedules"] = new_schedules
        await save_pyro_data()
        return await message.reply("✅ زمانبندی حذف شد.")

    # تنظیم متن پنل سفارشی
    if lower.startswith("تنظیم متن پنل"):
        arg = text.replace("تنظیم متن پنل", "", 1).strip()
        pyro_data["panel_text"] = arg
        await save_pyro_data()
        return await message.reply("✅ متن پنل ذخیره شد.")

# ==================== پاسخ خودکار Pyrogram ====================
@pyro_app.on_message(filters.text & ~filters.me)
@flood_protect
async def pyro_auto_keyword_react(client, message):
    txt = (message.text or "").lower()
    
    # keyword check
    for kw in pyro_data.get("keywords", []):
        if kw and kw.lower() in txt:
            try:
                await message.reply(f"🤖 پیام شامل '{kw}' شد.")
                break
            except Exception:
                pass

# ==================== اجرای اصلی ====================
async def main():
    # شروع Telethon
    await client.start()
    global OWNER_ID
    me_telethon = await client.get_me()
    OWNER_ID = me_telethon.id
    print(f"🤖 ربات Telethon آماده: {me_telethon.first_name} (@{me_telethon.username}) - ID: {me_telethon.id}")
    if main_group:
        print(f"🏠 گروه اصلی: {main_group}")
    
    # شروع Pyrogram
    await pyro_app.start()
    me_pyro = await pyro_app.get_me()
    print(f"🤖 ربات Pyrogram آماده: {me_pyro.first_name} (@{me_pyro.username}) - ID: {me_pyro.id}")
    
    # استارت تسک‌های پس‌زمینه
    client.loop.create_task(update_telethon_clock())
    client.loop.create_task(update_pyro_clock())
    client.loop.create_task(schedule_runner())
    
    print("✅ هر دو ربات فعال شدند!")
    print("📋 دستورات Telethon: 'پنل' را ارسال کنید")
    print("📋 دستورات Pyrogram: 'پنل پی' را ارسال کنید")
    
    await client.run_until_disconnected()

# ==================== مدیریت خاموشی ====================
def register_signal_handlers(loop):
    if platform.system() != "Windows":
        import signal
        def shutdown_handler():
            print("🛑 در حال خاموش شدن ...")
            asyncio.create_task(save_pyro_data())
            save_state()
        loop.add_signal_handler(signal.SIGINT, shutdown_handler)
        loop.add_signal_handler(signal.SIGTERM, shutdown_handler)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    register_signal_handlers(loop)
    
    try:
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("کلید قطع شد. ذخیره‌سازی ...")
        save_state()
        asyncio.run(save_pyro_data())