"""Coach Gary core logic: pure functions over a per-user state dict. No Telegram, no network."""
import json
import random
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
POOL = json.loads((DATA_DIR / "exercises.json").read_text())
LIB = json.loads((DATA_DIR / "reactions.json").read_text())

GOAL = 8
NO_REPEAT = 15
# Local-time slots, Mon–Fri. Each slot owns a body zone.
SLOTS = [(10, 0, "back"), (11, 30, "shoulders"), (13, 0, "neck"), (14, 30, "eyes"), (16, 0, "wrists"), (17, 30, "legs")]
WEEKLY_SUMMARY = (4, 18, 30)  # Friday 18:30

# Inline buttons under every reminder: callback code -> (label, intent, reason)
BUTTONS = {
    "done": ("✅ Done", "done", "none"),
    "water": ("💧 Drank water", "water", "none"),
    "call": ("📞 Was on a call", "skipped", "meeting"),
    "later": ("⏳ Later", "later", "none"),
    "lazy": ("😴 Too lazy", "skipped", "lazy"),
    "skip": ("🙅 Skip", "skipped", "none"),
}


def new_state():
    return {"date": None, "water": 0, "sent": 0, "done": 0, "streak": 0, "skip_streak": 0,
            "recent": [], "cursors": {}, "reply_cursors": {}, "last": None, "log": [], "paused": False}


def _roll_day(state, now):
    today = now.date().isoformat()
    if state.get("date") != today:
        state.update({"date": today, "water": 0, "sent": 0, "done": 0})


def due_slot(now):
    """Index of the slot starting at this exact local minute on a weekday, else None."""
    if now.weekday() > 4:
        return None
    for i, (h, m, _) in enumerate(SLOTS):
        if (now.hour, now.minute) == (h, m):
            return i
    return None


def is_weekly_summary(now):
    return (now.weekday(), now.hour, now.minute) == WEEKLY_SUMMARY


def _rotate(state, key, items):
    c = state["cursors"].get(key, 0)
    state["cursors"][key] = c + 1
    return items[c % len(items)]


def build_reminder(state, now, slot=None):
    """Pick the next exercise and build the caption. Mutates state. Returns (caption, image_url, exercise_id)."""
    _roll_day(state, now)
    if slot is None:  # on-demand (/stretch): use the nearest slot's zone
        minutes = now.hour * 60 + now.minute
        slot = min(range(len(SLOTS)), key=lambda i: abs(SLOTS[i][0] * 60 + SLOTS[i][1] - minutes))
    zone = SLOTS[slot][2]

    nag = None
    prev = state.get("last")
    if prev and prev.get("at", "")[:10] == state["date"] and not prev.get("replied"):
        state["skip_streak"] += 1
        state["streak"] = 0
        nag = _rotate(state, "ignored", LIB["reactions"]["ignored"]).replace("{skip_streak}", str(state["skip_streak"]))
        state["log"].append([prev["at"][:16], "ignored", "none"])

    rng = random.Random(now.isoformat())
    fresh = [p for p in POOL if p["zone"] == zone and p["id"] not in state["recent"]]
    ex = rng.choice(fresh or [p for p in POOL if p["zone"] == zone])

    intro = _rotate(state, "intro_" + zone, LIB["intros"][zone])
    water = _rotate(state, "water", LIB["water_lines"]).replace("{water}", str(state["water"])).replace("{goal}", str(GOAL))

    lines = ([nag, ""] if nag else []) + [intro, "", "<b>" + ex["name"] + "</b>"]
    lines += [f"{n}. {s}" for n, s in enumerate(ex["steps"], 1)]
    lines += [f"⏱ {ex['duration_sec']} sec", "", water]

    state["recent"] = (state["recent"] + [ex["id"]])[-NO_REPEAT:]
    state["sent"] += 1
    state["last"] = {"id": ex["id"], "zone": zone, "at": now.isoformat(), "replied": False}
    state["log"] = state["log"][-80:]
    return "\n".join(lines), ex["image_url"], ex["id"]


def jev_request(text, state):
    """(state_text, questions) for a Jev typed decision on a free-text reply."""
    last = state.get("last") or {}
    ctx = 'Coach bot sent a {} exercise reminder ({}). User replied: "{}"'.format(
        last.get("zone", "stretch"), last.get("id", ""), text)
    return ctx, LIB["jev_questions"]


def button_answers(code):
    _, intent, reason = BUTTONS[code]
    return {"intent": {"choice": intent, "confidence": 1}, "reason": {"choice": reason},
            "tone": {"choice": "neutral"}, "pain_mentioned": {"noul": 0}, "wants_pause": {"noul": 0}}


def _pick_line(state, key):
    """Cycle a bucket through a fixed shuffle so nothing repeats until the bucket is exhausted."""
    lines = LIB["reactions"][key]
    order = list(range(len(lines)))
    random.Random(key).shuffle(order)
    c = state["reply_cursors"].get(key, 0)
    state["reply_cursors"][key] = c + 1
    return lines[order[c % len(lines)]]


def react(state, answers, text, now):
    """Turn classified answers into Gary's reply. Mutates state. Returns (reply, bucket_key)."""
    _roll_day(state, now)
    intent = answers["intent"]["choice"]
    conf = answers["intent"].get("confidence", 1)
    reason, tone = answers["reason"]["choice"], answers["tone"]["choice"]
    pain, pause = answers["pain_mentioned"]["noul"], answers["wants_pause"]["noul"]
    reactions = LIB["reactions"]

    if state.get("paused") and re.search(r"\b(back|resume|unpause)\b", text.lower()):
        state["paused"] = False
        key = "safety.resume"
    elif pain >= 0.6:
        key = "safety.pain"
    elif reason == "sick":
        key = "safety.sick"
    elif pause >= 0.6:
        state["paused"] = True
        key = "safety.pause"
    elif conf < 0.5:
        key = "fallback.unclear"
    elif intent == "done":
        state["done"] += 1
        state["streak"] += 1
        state["skip_streak"] = 0
        if state["streak"] >= 3 and state["streak"] % 3 == 0:
            key = "streak.done"
        else:
            key = "done." + tone if "done." + tone in reactions else "done"
    elif intent == "water":
        state["water"] += 1
        key = "water.goal_hit" if state["water"] == GOAL else "water"
    elif intent == "partial":
        state["done"] += 1
        key = "partial"
    elif intent == "skipped":
        state["streak"] = 0
        state["skip_streak"] += 1
        if reason == "meeting":
            key = "skipped.meeting.trust"  # no calendar in the public bot: take their word
        elif state["skip_streak"] >= 3:
            key = "streak.skip"
        else:
            key = next(k for k in ("skipped.%s.%s" % (reason, tone), "skipped." + reason,
                                   "skipped." + tone, "skipped.none") if k in reactions)
    elif intent in reactions:
        key = intent
    else:
        key = "fallback.unclear"

    line = _pick_line(state, key)
    values = {"water": state["water"], "goal": GOAL, "done_today": state["done"], "sent_today": state["sent"],
              "streak": state["streak"], "skip_streak": state["skip_streak"]}
    for k, v in values.items():
        line = line.replace("{" + k + "}", str(v))

    if state.get("last") and intent not in ("banter", "question", "greeting"):
        state["last"]["replied"] = True
    state["log"].append([now.isoformat()[:16], intent, reason])
    state["log"] = state["log"][-80:]
    return line, key


def weekly_summary(state, now):
    """Plain-text Friday recap from the last 7 days of the log."""
    week = [r for r in state["log"] if (now - datetime.fromisoformat(r[0]).replace(tzinfo=now.tzinfo)).days < 7]
    done = sum(r[1] in ("done", "partial") for r in week)
    water = sum(r[1] == "water" for r in week)
    ignored = sum(r[1] == "ignored" for r in week)
    skipped = sum(r[1] == "skipped" for r in week)
    reasons = {}
    for r in week:
        if r[1] == "skipped" and r[2] != "none":
            reasons[r[2]] = reasons.get(r[2], 0) + 1
    top = max(reasons, key=reasons.get) if reasons else None
    lines = ["📋 <b>Coach Gary's weekly report</b>", "",
             f"✅ Stretches done: {done}", f"🙅 Skipped: {skipped}", f"👻 Ghosted: {ignored}", f"💧 Water logged: {water}"]
    if top:
        label = {"meeting": "meetings", "lazy": "pure laziness", "busy": "being 'busy'", "forgot": "forgetting",
                 "tired": "being tired", "eating": "snacks", "away": "not at your desk"}.get(top, top)
        lines += ["", f"Top excuse: <i>{label}</i>. Noted. Forever."]
    total = done + skipped + ignored
    if total:
        rate = done / total
        verdict = ("🏅 Honestly? Solid week. Don't let it go to your head." if rate >= 0.7 else
                   "🦐 Some effort detected. The shrimp is nervous." if rate >= 0.4 else
                   "🪑 Your chair had a great week. You, less so.")
        lines += ["", verdict]
    lines += ["", "See you Monday. Hydrate over the weekend. 🎺"]
    return "\n".join(lines)
