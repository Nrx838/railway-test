"""Coach Carter Telegram bot: stretch & water reminders with a grumpy gym-teacher persona.

Env: TELEGRAM_TOKEN (required), FLYMYAI_API_KEY (for free-text replies via Jev), DB_PATH (default ./gary.db).
"""
import json
import logging
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

import coach

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
log = logging.getLogger("gary")

JEV_URL = "https://api.flymy.ai/api/v1/flymyai/typesafe-jev-1_13/predict"
TIMEZONES = [("🗽", "New York", "America/New_York"), ("🌽", "Chicago", "America/Chicago"),
             ("⛰", "Denver", "America/Denver"), ("🌴", "Los Angeles", "America/Los_Angeles"),
             ("💂", "London", "Europe/London"), ("🥨", "Berlin", "Europe/Berlin"),
             ("🏰", "Moscow", "Europe/Moscow"), ("🏙", "Dubai", "Asia/Dubai"),
             ("🛺", "Delhi", "Asia/Kolkata"), ("🌏", "Singapore", "Asia/Singapore"),
             ("🗼", "Tokyo", "Asia/Tokyo"), ("🦘", "Sydney", "Australia/Sydney")]

db = sqlite3.connect(os.environ.get("DB_PATH", "gary.db"), check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, tz TEXT, state TEXT, name TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
db.commit()


# ---------- storage ----------

def load_user(chat_id):
    row = db.execute("SELECT tz, state FROM users WHERE chat_id=?", (chat_id,)).fetchone()
    if not row:
        return None, None
    return row[0], json.loads(row[1])


def save_user(chat_id, tz, state, name=None):
    db.execute("INSERT INTO users (chat_id, tz, state, name) VALUES (?,?,?,?) "
               "ON CONFLICT(chat_id) DO UPDATE SET tz=excluded.tz, state=excluded.state, "
               "name=COALESCE(excluded.name, users.name)", (chat_id, tz, json.dumps(state), name))
    db.commit()


def bump_meta(key, amount):
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    value = float(row[0]) + amount if row else amount
    db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?,?)", (key, str(value)))
    db.commit()


def meta(key):
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return float(row[0]) if row else 0.0


# ---------- keyboards ----------

def reply_buttons():
    """Stretch rows (r:*) and a water row (w:*); each group disappears once answered."""
    b = lambda prefix, table, code: InlineKeyboardButton(table[code][0], callback_data=f"{prefix}:{code}")
    return InlineKeyboardMarkup([
        [b("r", coach.BUTTONS, c) for c in ("done", "later")],
        [b("r", coach.BUTTONS, c) for c in ("call", "lazy", "skip")],
        [b("w", coach.WATER_BUTTONS, c) for c in ("yes", "no")],
    ])


def without_group(markup, prefix):
    """The same keyboard minus every row of the answered question."""
    rows = [row for row in (markup.inline_keyboard if markup else [])
            if not all(btn.callback_data.startswith(prefix + ":") for btn in row)]
    return InlineKeyboardMarkup(rows) if rows else None


def tz_buttons():
    """City + its current local time, so people just pick the button whose clock matches theirs."""
    def label(icon, city, zone):
        return f"{icon} {city} · {datetime.now(ZoneInfo(zone)).strftime('%H:%M')}"
    rows = [TIMEZONES[i:i + 2] for i in range(0, len(TIMEZONES), 2)]
    return InlineKeyboardMarkup([[InlineKeyboardButton(label(*t), callback_data="tz:" + t[2]) for t in row]
                                 for row in rows])


TZ_PROMPT = ("🕐 <b>What time is it where you are?</b>\n"
             "Tap the city whose clock matches yours. I only bark during your working hours: "
             "Mon–Fri, 10:00 to 17:30 your time.")


# ---------- Jev ----------

async def classify(text, state):
    """Free-text reply -> typed answers via FlyMyAI Jev. Returns None if unavailable."""
    key = os.environ.get("FLYMYAI_API_KEY")
    if not key:
        return None
    ctx, questions = coach.jev_request(text, state)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(JEV_URL, headers={"X-API-KEY": key},
                                  data={"state": ctx, "questions": json.dumps(questions)})
        r.raise_for_status()
        # The endpoint streams SSE ("data: {...}" lines); the last one carrying answers wins.
        out = None
        for line in r.text.splitlines():
            if line.startswith("data:"):
                chunk = json.loads(line[5:]).get("output_data") or {}
                if "answers" in chunk:
                    out = chunk
        if out is None:
            raise ValueError("no answers in Jev response: " + r.text[:200])
        bump_meta("jev_calls", 1)
        bump_meta("jev_usd", float(out.get("charge_usd") or 0))
        return out["answers"]
    except Exception:
        log.exception("Jev call failed")
        return None


# ---------- sending ----------

async def send_reminder(bot, chat_id, tz, state, slot=None):
    now = datetime.now(ZoneInfo(tz))
    caption, image, _ = coach.build_reminder(state, now, slot)
    await bot.send_photo(chat_id, photo=image, caption=caption, parse_mode=ParseMode.HTML,
                         reply_markup=reply_buttons())


async def tick(context: ContextTypes.DEFAULT_TYPE):
    """Runs every minute: fire due slots and Friday reports in each user's local time."""
    for chat_id, tz, raw in db.execute("SELECT chat_id, tz, state FROM users WHERE tz IS NOT NULL").fetchall():
        state = json.loads(raw)
        if state.get("paused"):
            continue
        now = datetime.now(ZoneInfo(tz))
        stamp = now.strftime("%Y-%m-%d %H:%M")
        if state.get("last_tick") == stamp:
            continue
        try:
            slot = coach.due_slot(now)
            if slot is not None:
                await send_reminder(context.bot, chat_id, tz, state, slot)
            elif coach.is_weekly_summary(now):
                await context.bot.send_message(chat_id, coach.weekly_summary(state, now), parse_mode=ParseMode.HTML)
            else:
                continue
        except Exception:
            log.exception("send failed for %s", chat_id)
        state["last_tick"] = stamp
        save_user(chat_id, tz, state)


# ---------- handlers ----------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tz, state = load_user(chat_id)
    save_user(chat_id, tz, state or coach.new_state(), update.effective_user.first_name)
    await update.message.reply_text(
        "🎺 <b>LISTEN UP, RECRUIT.</b> I'm Coach Carter. Twenty years in the Marines, ten teaching gym, "
        "and now I've been assigned to you and that sorry chair.\n\n"
        "Six times a workday you get a desk drill and a water check. Tap a button when it's done, "
        "or give me your excuse. I've heard them all, and I've laughed at every one.\n\n"
        "Fair warning: I swear and I roast. /clean if you're delicate, /spicy to bring me back.",
        parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(TZ_PROMPT, parse_mode=ParseMode.HTML, reply_markup=tz_buttons())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    chat_id = q.message.chat.id
    tz, state = load_user(chat_id)
    state = state or coach.new_state()
    kind, _, value = q.data.partition(":")

    if kind == "tz":
        save_user(chat_id, value, state)
        await q.answer("Got it")
        city = next(c for _, c, z in TIMEZONES if z == value)
        local = datetime.now(ZoneInfo(value)).strftime("%H:%M")
        await q.message.edit_text(f"🕐 Locked in: <b>{city} time</b> (it's {local} there now).", parse_mode=ParseMode.HTML)
        await q.message.reply_text(
            "📋 <b>Your schedule, recruit</b>\n"
            "10:00 back · 11:30 shoulders · 13:00 neck\n14:30 eyes · 16:00 wrists · 17:30 legs\n"
            "Friday 18:30: weekly report. Weekends off.\n\n"
            "Can't wait? /stretch gets you one right now.\n"
            "/pause to shut me up · /stats for the damage report · /start to change city",
            parse_mode=ParseMode.HTML)
        return

    if kind in ("r", "w"):
        if tz is None:
            await q.answer("Pick your city first: /start")
            return
        table = coach.BUTTONS if kind == "r" else coach.WATER_BUTTONS
        if value not in table:  # button from an older keyboard layout
            await q.answer("That drill expired. /stretch for a fresh one.")
            await q.edit_message_reply_markup(None)
            return
        label = table[value][0]
        now = datetime.now(ZoneInfo(tz))
        reply, _ = coach.react(state, coach.button_answers(value), label, now)
        save_user(chat_id, tz, state)
        await q.answer(label)
        await q.edit_message_reply_markup(without_group(q.message.reply_markup, kind))  # one answer per question
        await q.message.reply_text(reply)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tz, state = load_user(chat_id)
    if tz is None:
        await update.message.reply_text(TZ_PROMPT, parse_mode=ParseMode.HTML, reply_markup=tz_buttons())
        return
    text = update.message.text
    answers = coach.quick_answers(text) or await classify(text, state)
    if answers is None:
        answers = {"intent": {"choice": "other", "confidence": 0}, "reason": {"choice": "none"},
                   "tone": {"choice": "neutral"}, "pain_mentioned": {"noul": 0}, "wants_pause": {"noul": 0}}
    reply, key = coach.react(state, answers, text, datetime.now(ZoneInfo(tz)))
    log.info("reply %s -> %s", chat_id, key)
    save_user(chat_id, tz, state)
    await update.message.reply_text(reply)


async def cmd_stretch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tz, state = load_user(chat_id)
    if tz is None:
        await update.message.reply_text(TZ_PROMPT, parse_mode=ParseMode.HTML, reply_markup=tz_buttons())
        return
    await send_reminder(context.bot, chat_id, tz, state)
    save_user(chat_id, tz, state)


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz, state = load_user(update.effective_chat.id)
    if state is None:
        return
    state["paused"] = True
    save_user(update.effective_chat.id, tz, state)
    await update.message.reply_text("⏸️ Fine. Pausing. /resume when you miss me. You will.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz, state = load_user(update.effective_chat.id)
    if state is None:
        return
    state["paused"] = False
    save_user(update.effective_chat.id, tz, state)
    await update.message.reply_text("📣 Back on. Your spine filed three complaints while I was gone.")


async def set_mode(update: Update, mode: str, text: str):
    tz, state = load_user(update.effective_chat.id)
    if state is None:
        return
    state["mode"] = mode
    save_user(update.effective_chat.id, tz, state)
    await update.message.reply_text(text)


async def cmd_clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mode(update, "clean", "🧼 Clean mode. No swearing, no roasting. Still yelling, though.")


async def cmd_spicy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mode(update, "spicy", "🌶 Spicy mode, hell yes. Gloves are off, recruit.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz, state = load_user(update.effective_chat.id)
    if tz is None:
        return
    now = datetime.now(ZoneInfo(tz))
    await update.message.reply_text(coach.weekly_summary(state, now), parse_mode=ParseMode.HTML)


async def cmd_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """What Carter's brain has cost so far (all users)."""
    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await update.message.reply_text(
        f"🧠 Jev calls: {int(meta('jev_calls'))}\n💵 Total spent: ${meta('jev_usd'):.5f}\n👥 Victims: {users}")


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("stretch", "Get a stretch right now"),
        BotCommand("stats", "This week's damage report"),
        BotCommand("pause", "Make Carter stop (for now)"),
        BotCommand("resume", "Bring Carter back"),
        BotCommand("clean", "No swearing, no roasting"),
        BotCommand("spicy", "Gloves off (default)"),
        BotCommand("start", "Start over / change time zone"),
    ])


def main():
    app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stretch", cmd_stretch))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("clean", cmd_clean))
    app.add_handler(CommandHandler("spicy", cmd_spicy))
    app.add_handler(CommandHandler("cost", cmd_cost))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.job_queue.run_repeating(tick, interval=30, first=5)
    log.info("Coach Carter is on duty")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
