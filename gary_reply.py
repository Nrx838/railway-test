"""Coach Gary responder logic. Run with args.json in the cwd; prints one JSON object.

mode "jev":   {"mode":"jev","text":..., "last":{...}}  -> {"state": str, "questions": {...}} for Jev
mode "react": {"mode":"react","text":..., "answers":{...Jev answers...}, "state":{...},
               "events":[{"start":iso,"end":iso}], "now":iso}
              -> {"reply": str|null, "llm": bool, "llm_hint": str, "state": {...}}
"""
import json, random, re, urllib.request
from datetime import datetime

LIB_URL = "https://raw.githubusercontent.com/Nrx838/railway-test/6c507d8d34c3b192740ba77203b3be3872388d92/reactions.json"
GOAL = 8


def load_lib():
    with urllib.request.urlopen(LIB_URL, timeout=20) as r:
        return json.load(r)


# Persistent reply-keyboard buttons: known text, so no Jev call needed.
BUTTONS = {
    "✅ Done": ("done", "none"),
    "💧 Drank water": ("water", "none"),
    "📞 Was on a call": ("skipped", "meeting"),
    "⏳ Later": ("later", "none"),
    "😴 Too lazy": ("skipped", "lazy"),
    "🙅 Skip": ("skipped", "none"),
}


def button_answers(text):
    intent, reason = BUTTONS[text.strip()]
    return {"intent": {"choice": intent, "confidence": 1}, "reason": {"choice": reason},
            "tone": {"choice": "neutral"}, "pain_mentioned": {"noul": 0}, "wants_pause": {"noul": 0}}


def jev_payload(args, lib):
    if args["text"].strip() in BUTTONS:
        return {"shortcut": True, "answers": button_answers(args["text"])}
    last = args.get("last") or {}
    ctx = "Coach bot sent a {} exercise reminder ({}). User replied: \"{}\"".format(
        last.get("zone", "stretch"), last.get("id", ""), args["text"])
    return {"state": ctx, "questions": lib["jev_questions"]}


def pick(lib, state, key):
    """Next line from a bucket, cycling through a fixed shuffle so nothing repeats until the bucket is exhausted."""
    lines = lib["reactions"][key]
    order = list(range(len(lines)))
    random.Random(key).shuffle(order)
    c = state.setdefault("reply_cursors", {}).get(key, 0)
    state["reply_cursors"][key] = c + 1
    return lines[order[c % len(lines)]]


def meeting_check(args, state, now):
    """Did a calendar event overlap the time between the last reminder and now?"""
    last_at = datetime.fromisoformat(state.get("last", {}).get("at", now.isoformat()))
    best = None
    for e in args.get("events") or []:
        s, t = datetime.fromisoformat(e["start"]), datetime.fromisoformat(e["end"])
        if s < now and t > last_at:
            best = (s, t) if best is None or t > best[1] else best
    gap_min = int((now - last_at).total_seconds() // 60)
    if not best:
        return False, {"gap_min": gap_min, "meeting_min": 0, "ended_ago": 0}
    s, t = best
    return True, {"gap_min": gap_min, "meeting_min": int((t - s).total_seconds() // 60),
                  "ended_ago": max(0, int((now - t).total_seconds() // 60))}


def react(args, lib):
    state = args.get("state") or {}
    now = datetime.fromisoformat(args["now"])
    today = now.date().isoformat()
    if state.get("date") != today:
        state.update({"date": today, "water": 0, "sent": 0, "done": 0})
    for k in ("streak", "skip_streak"):
        state.setdefault(k, 0)

    a = args["answers"]
    intent, conf = a["intent"]["choice"], a["intent"].get("confidence", 1)
    reason, tone = a["reason"]["choice"], a["tone"]["choice"]
    pain, pause = a["pain_mentioned"]["noul"], a["wants_pause"]["noul"]
    text = args["text"].lower()
    v = {}
    llm = False

    if state.get("paused") and re.search(r"\b(back|resume|start|unpause)\b", text):
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
    elif intent in ("banter", "question"):
        llm, key = True, intent
    elif intent == "done":
        state["done"] += 1
        state["streak"] += 1
        state["skip_streak"] = 0
        key = "streak.done" if state["streak"] >= 3 and state["streak"] % 3 == 0 else (
            "done." + tone if "done." + tone in lib["reactions"] else "done")
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
            ok, v = meeting_check(args, state, now)
            key = "skipped.meeting." + ("confirmed" if ok else "unconfirmed")
        elif state["skip_streak"] >= 3:
            key = "streak.skip"
        else:
            key = next(k for k in ("skipped.%s.%s" % (reason, tone), "skipped." + reason,
                                   "skipped." + tone, "skipped.none") if k in lib["reactions"])
    elif intent in lib["reactions"]:
        key = intent
    else:
        key = "fallback.unclear"

    line = pick(lib, state, key)
    v.update({"water": state["water"], "goal": GOAL, "done_today": state["done"],
              "sent_today": state.get("sent", 0), "streak": state["streak"],
              "skip_streak": state["skip_streak"]})
    for k, val in v.items():
        line = line.replace("{" + k + "}", str(val))

    state.setdefault("last", {})["replied"] = True
    log = state.setdefault("log", [])
    # Compact rows for the Friday chart: [time, intent, reason]. A week is ~40 rows.
    log.append([now.isoformat()[:16], intent, reason])
    state["log"] = log[-60:]

    hint = ("Reply as Coach Gary: tired, sarcastic, secretly caring 30-year gym teacher. "
            "1-2 short sentences, one emoji, English, no medical advice, steer back to the stretch.")
    print(json.dumps({"reply": line, "llm": llm, "llm_hint": hint if llm else "", "key": key,
                      "state": state}, ensure_ascii=False))


def main():
    args = json.load(open("args.json"))
    lib = load_lib()
    if args["mode"] == "jev":
        print(json.dumps(jev_payload(args, lib), ensure_ascii=False))
    else:
        react(args, lib)


main()
