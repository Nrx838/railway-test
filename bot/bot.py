"""Coach Gary Telegram bot: stretch & water reminders with a grumpy gym-teacher persona.

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
log = logging.getLogger("gary")

JEV_URL = "https://api.flymy.ai/api/v1/flymyai/typesafe-jev-1_13/predict"
TIMEZONES = [("🗽 ET", "America/New_York"), ("🌽 CT", "America/Chicago"), ("⛰ MT", "America/Denver"),
             ("🌴 PT", "America/Los_Angeles"), ("💂 London", "Europe/London"), ("🥨 Berlin", "Europe/Berlin"),
             ("🏙 Dubai", "Asia/Dubai"), ("🌏 Singapore", "Asia/Singapore")]

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
    codes = list(coach.BUTTONS)
    rows = [codes[i:i + 2] for i in range(0, len(codes), 2)]
    return InlineKeyboardMarkup([[InlineKeyboardButton(coach.BUTTONS[c][0], callback_data="r:" + c) for c in row]
                                 for row in rows])


def tz_buttons():
    rows = [TIMEZONES[i:i + 2] for i in range(0, len(TIMEZONES), 2)]
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="tz:" + zone) for label, zone in row]
                                 for row in rows])


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
        body = r.json()
        out = body.get("output_data", body)
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
        "🎺 <b>Coach Gary here.</b> 30 years of teaching gym, and now I've been assigned to you and your chair.\n\n"
        "Six times a workday I'll send you a quick desk stretch and nag you about water. "
        "Tap a button when you're done, or tell me your excuse. I've heard them all.",
        parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("📍 First: where are you? I only yell during your working hours.",
                                    reply_markup=tz_buttons())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    chat_id = q.message.chat.id
    tz, state = load_user(chat_id)
    state = state or coach.new_state()
    kind, _, value = q.data.partition(":")

    if kind == "tz":
        save_user(chat_id, value, state)
        await q.answer("Got it")
        await q.edit_message_reply_markup(None)
        await q.message.reply_text(
            f"📍 {value.split('/')[-1].replace('_', ' ')} time it is. First drill at 10:00, last one at 17:30, Mon–Fri.\n"
            "Can't wait? Hit /stretch for one right now.\n\n/pause to shut me up, /stats for the damage report.")
        return

    if kind == "r":
        if tz is None:
            await q.answer("Pick a time zone first: /start")
            return
        now = datetime.now(ZoneInfo(tz))
        reply, _ = coach.react(state, coach.button_answers(value), coach.BUTTONS[value][0], now)
        save_user(chat_id, tz, state)
        await q.answer(coach.BUTTONS[value][0])
        await q.edit_message_reply_markup(None)  # one answer per reminder
        await q.message.reply_text(reply)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tz, state = load_user(chat_id)
    if tz is None:
        await update.message.reply_text("📍 Tell me your time zone first.", reply_markup=tz_buttons())
        return
    text = update.message.text
    answers = await classify(text, state)
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
        await update.message.reply_text("📍 Time zone first.", reply_markup=tz_buttons())
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


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz, state = load_user(update.effective_chat.id)
    if tz is None:
        return
    now = datetime.now(ZoneInfo(tz))
    await update.message.reply_text(coach.weekly_summary(state, now), parse_mode=ParseMode.HTML)


async def cmd_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """What Gary's brain has cost so far (all users)."""
    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await update.message.reply_text(
        f"🧠 Jev calls: {int(meta('jev_calls'))}\n💵 Total spent: ${meta('jev_usd'):.5f}\n👥 Victims: {users}")


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("stretch", "Get a stretch right now"),
        BotCommand("stats", "This week's damage report"),
        BotCommand("pause", "Make Gary stop (for now)"),
        BotCommand("resume", "Bring Gary back"),
        BotCommand("start", "Start over / change time zone"),
    ])


def main():
    app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stretch", cmd_stretch))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("cost", cmd_cost))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.job_queue.run_repeating(tick, interval=30, first=5)
    log.info("Coach Gary is on duty")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
