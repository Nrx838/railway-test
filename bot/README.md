# Coach Gary bot

Grumpy gym-teacher Telegram bot: 6 desk stretches per workday, water nagging, excuses judged by
FlyMyAI Jev (typed classifier, ~$0.00003 per free-text reply). Buttons need no model call at all.

## Run locally
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    TELEGRAM_TOKEN=... FLYMYAI_API_KEY=... .venv/bin/python bot.py

## Railway
Root directory `bot/`, start command `python bot.py` (railway.json). Variables: `TELEGRAM_TOKEN`,
`FLYMYAI_API_KEY`, `DB_PATH=/data/gary.db` with a volume mounted at `/data`.

Commands: /start /stretch /stats /pause /resume, and /cost for total Jev spend.
Exercise photos: free-exercise-db (public domain) + generated set in `../img`.
