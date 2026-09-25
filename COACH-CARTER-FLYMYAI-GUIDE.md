# Coach Carter: как собрать агента-тренера на FlyMyAI

Полный разбор кейса: идея, контент, логика, два варианта сборки (полностью на агентах FlyMyAI и рабочий: бэкенд на Fly.io + Jev через FlyMyAI), грабли, цены, медиа и промо-ролик. Документ написан так, чтобы по нему можно было повторить всё с нуля.

> **Состояние на 25.09.2026.** Рабочая архитектура — вариант B: Python-бот на **Fly.io** плюс Jev через API FlyMyAI. На Fly.io бот поднимается одной командой, `bot/deploy-fly.sh`. На момент написания он ещё работает локально: нужен вход в аккаунт Fly. Вариант A, полностью на агентах FlyMyAI, собран и протестирован, но **выключен из-за цены**: $0.15–0.25 за запуск. Код лежит на GitHub: `Nrx838/railway-test`, ветка `coach-gary`.

---

## Содержание
1. [Идея](#1-идея)
2. [Что получилось](#2-что-получилось)
3. [Персонаж и контент](#3-персонаж-и-контент)
4. [Пул упражнений и картинки](#4-пул-упражнений-и-картинки)
5. [Логика бота](#5-логика-бота)
6. [Jev: классификатор ответов](#6-jev-классификатор-ответов)
7. [Вариант A: полностью на агентах FlyMyAI](#7-вариант-a-полностью-на-агентах-flymyai)
8. [Вариант B: бэкенд на Fly.io + Jev через FlyMyAI (рабочий)](#8-вариант-b-бэкенд-на-flyio--jev-через-flymyai-рабочий)
9. [Грабли и обходные пути](#9-грабли-и-обходные-пути)
10. [Чего не хватает FlyMyAI](#10-чего-не-хватает-flymyai)
11. [Медиа через FlyMyAI](#11-медиа-через-flymyai)
12. [Промо-ролик и обложка](#12-промо-ролик-и-обложка)
13. [Цены](#13-цены)
14. [Приложение: ID и ссылки этого аккаунта](#14-приложение-id-и-ссылки-этого-аккаунта)

---

## 1. Идея

**Задача:** напоминать попить воды и размяться, чтобы не сидеть весь день креветкой за компом.

**Почему не просто таймер.** Таймер умеет «пей воду каждый час», и всё. Ценность появляется, когда бот:
- присылает **каждый раз новое упражнение с картинкой** и подбирает его под время дня (утром спина, после обеда шея, вечером ноги);
- **понимает ответ человека**: «сделал», «был на созвоне», «лень», «болит шея» — и отвечает в характере;
- **ведёт статистику**: вода, разминки, серии, пятничный отчёт;
- **работает для многих людей**: у каждого свой часовой пояс.

**Изюминка кейса для поста.** «Мозг» бота — **Jev**, типизированный классификатор на FlyMyAI за **$0.00003** за разбор ответа. Реплики берутся из готовой библиотеки, а не генерируются LLM. Поэтому AI-счёт за месяц меньше цента, а весь бот стоит около $2 в месяц вместе с хостингом.

**Как шла работа:**
1. Выбрали персонажа: сначала ворчливый физрук «Палыч» / Coach Gary, потом бывший морпех Coach Carter в духе Майора Пейна.
2. Собрали на агентах FlyMyAI: напоминалка плюс ответчик. Всё работало, но один запуск стоит $0.15–0.25, поэтому выключили.
3. Сделали гибрид: свой Python-бот с бэкендом на Fly.io, Jev через REST API FlyMyAI, inline-кнопки.
4. Сделали англоязычную многопользовательскую версию, чтобы делиться ссылкой.
5. Сделали промо-ролик в пиксель-арте (Remotion) и обложку для X.

---

## 2. Что получилось

| Что | Где |
|---|---|
| Бот (бэкенд на Fly.io, рабочий) | `/home/nrx83/AI/coach-gary/bot/` · GitHub `Nrx838/railway-test@coach-gary`, папка `bot/` |
| Код для агентов FlyMyAI | `gary_pick.py`, `gary_reply.py` в корне ветки `coach-gary` (закреплённые коммиты, см. §7) |
| Библиотека реплик | `bot/reactions.json` (671 реплика) · источник `drill_lines.py` |
| Пул упражнений | `bot/exercises.json` (65 упражнений) · сборка `build_pool.py` · картинки `img/` |
| Бэкенд Fly.io | `bot/Dockerfile`, `bot/fly.toml`, `bot/deploy-fly.sh` · локально для разработки `bot/run.sh` |
| Промо-ролик | `/home/nrx83/AI/remotion/my-video/out/coach-carter-v4.mp4` (1:14, 1920×1080) |
| Обложка для X | `/home/nrx83/AI/remotion/my-video/out/coach-carter-cover.jpg` |
| Сценарий ролика | `/home/nrx83/AI/remotion/coach-carter-video-final.md` |

---

## 3. Персонаж и контент

### Coach Carter
Бывший морпех, теперь тренер в школьном спортзале, «приставлен» к одному офисному работнику. Громкий, абсурдные армейские угрозы, суровая любовь. Втайне заботится.

- **Внешность** (для генерации картинок): широкие плечи, квадратная челюсть, седой ёжик, седые усы-подкова, тёмно-синий спортивный костюм с белой полосой, **красный свисток на шнурке**, жетоны, татуировка-якорь, армейские ботинки, клипборд. Официальную эмблему USMC не использовать: это охраняемый знак.
- **Обращения:** recruit, soldier, private. **Слова-маркеры:** canteen, drill, AWOL, shrimp posture.

### Жёсткие правила контента
- **Можно:** мат (только в «острых» репликах), роаст, шутки про еду, пончики и то, что стул просит надбавку за вредность.
- **Нельзя:** советовать не есть или голодать, давать медицинские советы, шутить над болью и болезнью.
- **Боль, болезнь и пауза** отдельно: ответ прямой и заботливый («Real pain = real doctor»).

### Библиотека `reactions.json`
**671 реплика в 33 категориях**, из них 315 «острых». Острые помечены префиксом `[x] ` и показываются только в режиме `spicy`, который включён по умолчанию. В `/clean` их нет, и ни одна категория при этом не остаётся пустой.

| Категория | Когда | Кол-во |
|---|---|---|
| `safety.pain` / `safety.sick` / `safety.pause` / `safety.resume` | боль, болезнь, просьба о паузе, возвращение | 8 / 8 / 8 / 8 |
| `done`, `done.proud`, `done.sarcastic`, `done.annoyed` | сделал, с разным тоном | 46 / 15 / 17 / 15 |
| `partial` | сделал частично | 20 |
| `water`, `water.goal_hit`, `water.no` | выпил / 8 из 8 / не выпил | 33 / 10 / 18 |
| `skipped.meeting.trust` | был на созвоне (версия без календаря) | 25 |
| `skipped.lazy` (+ `.sarcastic`, `.apologetic`) | лень | 40 / 15 / 15 |
| `skipped.forgot` / `.busy` / `.tired` / `.eating` / `.away` / `.none` / `.annoyed` | другие причины | 20 / 28 / 23 / 18 / 10 / 31 / 15 |
| `later` | «потом» | 29 |
| `banter`, `question`, `complaint`, `greeting`, `rude` | болтовня, вопрос, жалоба, привет, грубость | 23 / 15 / 20 / 15 / 38 |
| `ignored` | не ответил на прошлое напоминание | 36 |
| `streak.done`, `streak.skip` | серии | 15 / 24 |
| `fallback.unclear` | Jev не уверен | 10 |

**Плюс:** 78 вступлений к упражнениям, по 12–14 на каждую зону тела, и 12 строк про воду.

**Переменные внутри реплик:** `{water}`, `{goal}`, `{done_today}`, `{sent_today}`, `{streak}`, `{skip_streak}`.

**Злые эмодзи** (😤 😠 😡 🤬 💢 👿 🔥 💀 🫵 😈 🪖 👊) дописываются автоматически при сборке, детерминированно: острым репликам в ~80% случаев, остальным в ~50%. Категориям `safety.*` не добавляются.

**Версия с календарём.** У старой библиотеки Coach Gary, которую использует вариант A, есть ещё `skipped.meeting.confirmed` и `skipped.meeting.unconfirmed`. Это «календарь подтвердил» и «календарь пуст, ты врёшь». Лежат в `reactions.json` на коммите `6c507d8`.

---

## 4. Пул упражнений и картинки

**65 упражнений** (`exercises.json`). У каждого есть `id`, `name`, `zone`, `where` (seated / standing / wall), `duration_sec`, `difficulty`, `steps` (3 коротких шага), `image_url`.

| Зона | Слот | Кол-во |
|---|---|---|
| back | 10:00 | 12 |
| shoulders | 11:30 | 17 |
| neck | 13:00 | 12 |
| eyes | 14:30 | 6 |
| wrists | 16:00 | 6 |
| legs | 17:30 | 12 |

**Источники:**
- **38 упражнений из free-exercise-db** (github.com/yuhonas/free-exercise-db, public domain). Взяты растяжки, которые можно сделать у стола. Картинка берётся так: `https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{id}/1.jpg`. Кадр `1.jpg` показывает конечную позу, он понятнее стартового.
- **27 своих упражнений** (глаза, кисти, шея, плечи). Картинки сгенерированы **GPT Image на FlyMyAI** двумя сетками (4×4 и 4×3) в стиле фото из базы: тот же парень, тот же зал. Сетки нарезаны скриптом, лежат в `img/`, раздаются с GitHub: `https://raw.githubusercontent.com/Nrx838/railway-test/coach-gary/img/{id}.jpg`.
- **Шаги упражнений** переписаны коротко, по 3 штуки, чтобы подпись в Telegram была читаемой (лимит подписи 1024 символа).

**Как нарезать сетку:** обрезать ячейки по белым разделителям, срезать сверху ~34–40 px с подписью ячейки, увеличить в 2 раза с LANCZOS (см. §11).

---

## 5. Логика бота

### Расписание (местное время пользователя, пн–пт)
`10:00` спина → `11:30` плечи → `13:00` шея → `14:30` глаза → `16:00` кисти → `17:30` ноги. Отчёт приходит в пятницу в 18:30, выходные без напоминаний.

### Напоминание
1. Сбросить дневные счётчики, если наступил новый день.
2. **Проверить прошлое напоминание.** Если на упражнение не ответили, это «призрак»: `skip_streak += 1`, серия обнуляется, в начало сообщения идёт строка из `ignored`.
3. **Выбрать упражнение** по зоне слота, исключив последние 15 отправленных. Случайный выбор с сидом от времени, поэтому детерминированный.
4. **Собрать подпись:**
   - вступление зоны, по кругу;
   - **название** и 3 шага;
   - `⏱ N sec`;
   - строка про воду («Glass {water} of {goal}…»);
   - `👇 Stretch done? Water in?`.
5. **Отправить** картинку с подписью (HTML) и двумя группами кнопок.

### Кнопки: два независимых вопроса
```
[✅ Done] [⏳ Later]
[📞 Call] [😴 Lazy] [🙅 Skip]        ← вопрос про упражнение, callback r:<code>
[💧 Drank a glass] [🚱 Not yet]      ← вопрос про воду, callback w:<code>
```
- Нажатие в группе убирает **только её ряды**. Когда отвечены обе, клавиатура исчезает целиком.
- **Вода не закрывает упражнение.** Если про упражнение не ответили, следующее напоминание начнётся с 👻.
- Кнопки со старых раскладок бот не обрабатывает, а отвечает «That drill expired».

### Свободный текст
1. **Быстрые ответы без модели:** `+`, `done`, `did it`, `yes`, `ok`, `✅` → done · `water`, `drank`, `💧` → вода · `-`, `no`, `nope`, `not done`, `nah`, `skip` → пропуск.
2. **Всё остальное уходит в Jev** (§6), он возвращает `intent`, `reason`, `tone`, `pain_mentioned`, `wants_pause`.
3. **Выбор категории, по приоритету:**
   1. на паузе и в тексте «back / resume / unpause» → `safety.resume`;
   2. `pain_mentioned ≥ 0.6` → `safety.pain`;
   3. `reason = sick` → `safety.sick`;
   4. `wants_pause ≥ 0.6` → `safety.pause`, бот ставит паузу;
   5. уверенность `intent < 0.5` → `fallback.unclear`;
   6. `done`: done +1, streak +1. Каждый 3-й подряд → `streak.done`, иначе `done.<tone>` или `done`;
   7. `water`: вода +1. На 8/8 → `water.goal_hit`, иначе `water`;
   8. `water_no` → `water.no`;
   9. `partial` → `partial`;
   10. `skipped`: streak = 0, skip_streak +1. Если `reason = meeting` → `skipped.meeting.trust`; при `skip_streak ≥ 3` → `streak.skip`; иначе первая существующая из `skipped.<reason>.<tone>` → `skipped.<reason>` → `skipped.<tone>` → `skipped.none`;
   11. `tone = annoyed` и `intent` из complaint / banter / other → `rude`;
   12. `intent` совпадает с названием категории (later, banter, question, complaint, greeting) → она;
   13. иначе `fallback.unclear`.
4. **Внутри категории** реплики идут по кругу в фиксированном перемешанном порядке, свой курсор на каждую категорию. Повтор возможен только после того, как пройдены все.
5. Подставить переменные, записать в лог `[время, intent, reason]` (последние 80 строк).

### Состояние пользователя (JSON в SQLite)
```json
{"date":"2026-09-25","water":3,"sent":4,"done":2,"streak":1,"skip_streak":0,
 "recent":["Chin_Tucks","..."],"cursors":{"intro_neck":2,"water":4,"ignored":1},
 "reply_cursors":{"done":3,"later":1},"last":{"id":"Chin_Tucks","zone":"neck","at":"...","replied":false},
 "log":[["2026-09-25T13:05","skipped","meeting"]],"paused":false,"mode":"spicy","last_tick":"2026-09-25 13:00"}
```

### Пятничный отчёт и `/stats`
Лог за 7 дней: сделано, пропущено, проигнорировано, выпито, «сухих» ответов про воду, главная отмазка. В конце вердикт по доле сделанного: ≥70%, ≥40% или меньше.

### Команды
- `/start` — приветствие и выбор города: 12 кнопок с **текущим временем** в каждом городе (New York, Chicago, Denver, Los Angeles, London, Berlin, Moscow, Dubai, Delhi, Singapore, Tokyo, Sydney);
- `/stretch` — упражнение прямо сейчас;
- `/stats` — статистика;
- `/pause` / `/resume`;
- `/clean` / `/spicy` — без мата или с ним;
- `/cost` — сколько всего потрачено на Jev.

---

## 6. Jev: классификатор ответов

**Модель:** `flymyai/typesafe-jev-1_13` (TypeSafe Jev 1.13). Отвечает на типизированные вопросы: `choice` (выбор варианта), `noul` (вероятность да/нет), `score` (оценка по шкале). Текст не генерирует.

**Цена:** $0.042 за 1M входных токенов, выход бесплатный. Реальный вызов на наши 5 вопросов: 707 токенов, **$0.000029694**.

### Вопросы (`jev_questions` в `reactions.json`)
```json
{
 "intent": {"type":"choice","instructions":"What is the user's reply about the reminder?","criteria":{
   "done":"did the exercise fully","partial":"did some of it","water":"drank water","skipped":"did not do it",
   "later":"asks to postpone or bargains","banter":"jokes or chats with the coach, not about the exercise",
   "question":"asks the coach a question","complaint":"complains about the bot or frequency","greeting":"just says hi","other":null}},
 "reason": {"type":"choice","instructions":"If skipped or partial, why?","criteria":{
   "meeting":"call, zoom, meeting, standup","lazy":"doesn't want to","forgot":null,"busy":"work, deadline",
   "tired":null,"sick":null,"eating":null,"away":"not at desk, commuting","none":"no reason given"}},
 "tone": {"type":"choice","instructions":"Tone of the reply","criteria":{
   "friendly":null,"sarcastic":null,"annoyed":null,"apologetic":null,"proud":null,"neutral":null}},
 "pain_mentioned": {"type":"noul","instructions":"Does the user mention real pain or physical discomfort?"},
 "wants_pause": {"type":"noul","instructions":"Does the user ask to stop or pause reminders?"}
}
```
**state**, то есть контекст для Jev: `Coach bot sent a neck exercise reminder (Chin_Tucks). User replied: "<текст>"`.

**Пример:** на «lol nope, stuck in a zoom since 10, my neck is actually killing me tbh» Jev вернул `skipped` (0.96), `meeting` (1.0), `pain_mentioned` 0.97. Бот выбрал `safety.pain`.

### Три способа вызвать
| Откуда | Как | Работает? |
|---|---|---|
| MCP FlyMyAI (Claude Code и т.п.) | `make_typed_decision(state, questions)` | ✅ |
| Внутри агента FlyMyAI | инструмент **`typesafe_jev.decide`** (подключить к агенту по ID) | ✅ |
| Внутри агента через `run_model` | `flymy-mcp.run_model` с Jev | ❌ **HTTP 403** |
| REST из своего кода | `POST https://api.flymy.ai/api/v1/flymyai/typesafe-jev-1_13/predict` | ✅ |

### REST: ответ приходит потоком (SSE)
Форма: `state` (строка), `questions` (JSON-строка), заголовок `X-API-KEY`. Ответ приходит строками `data: {...}`, а не обычным JSON. `r.json()` на нём падает.
```python
r = httpx.post(JEV_URL, headers={"X-API-KEY": key},
               data={"state": ctx, "questions": json.dumps(questions)}, timeout=30)
out = None
for line in r.text.splitlines():
    if line.startswith("data:"):
        chunk = json.loads(line[5:]).get("output_data") or {}
        if "answers" in chunk:
            out = chunk
answers = out["answers"]          # {"intent": {"choice": "...", "confidence": 0.96, ...}, ...}
cost = float(out.get("charge_usd") or 0)
```

---

## 7. Вариант A: полностью на агентах FlyMyAI

Два агента на DeepSeek V4.1 Flash, код в sandbox, память FlyMyAI, расписание cron. **Работает, но дорого** (§7.8). Подойдёт, когда у платформы появятся дешёвые функции без LLM и триггеры (§10).

### 7.1 Коннекторы
| Коннектор | Зачем | Как подключить |
|---|---|---|
| `telegram_bot` | отправка (`send_photo`, `send_message`) и приём (`get_updates`) | создать бота в @BotFather, токен вставить в FlyMyAI **через интерфейс**. Коннектор `telegram` (личный аккаунт) не подходит |
| `googlecalendar` | «идёт ли сейчас встреча» и проверка отмазок | OAuth в FlyMyAI |
| `sandbox` | запуск Python (`execute_code`) | обычно уже есть |
| `typesafe_jev` | классификация ответов (`decide`) | обычно уже есть |
| память (`system-utils`) | `get_memory_items`, `put_memory_item` | встроена в агента |

**ID коннекторов** для `available_tools` агента: `list_configured_tools(mcp_tool="telegram_bot")` и т.д. Нужен числовой `id`. Слаги не принимаются.

⚠️ **После переподключения ID меняется.** У нас `3428` превратился в `3430`, и `create_agent` падал с ошибкой «Invalid pk». Пока проверка подключения висит в статусе `verification_pending`, прикрепить коннектор может не получиться.

**chat_id** проще всего узнать так: написать боту и вызвать `get_updates` без `offset`. Без `offset` сообщения не помечаются прочитанными.

### 7.2 Код: GitHub, закреплённый коммит
Логику держим в коде, а не в промпте. Так выбор упражнения детерминирован, нет повторов и нет галлюцинаций.

**Как код попадает в агента.** Агент качает файл по ссылке **на конкретный коммит** и запускает в sandbox. Подменить код новым коммитом в ветку при этом нельзя.
- `https://raw.githubusercontent.com/Nrx838/railway-test/93867426a893278f6dcd27ea0cbeb08be8d102a2/gary_pick.py`
- `https://raw.githubusercontent.com/Nrx838/railway-test/93867426a893278f6dcd27ea0cbeb08be8d102a2/gary_reply.py`

**Почему не `code-blocks`.** Инструменты `code-blocks` и `flymy-mcp` встроены в агента, `add_tool` для них возвращает «недоступен». Передать 16 КБ кода в агента текстом тоже не вышло: запрос с большим параметром падал на коннекторе.

**Проверка безопасности.** Инструкцию «скачай код с GitHub и выполни» автоматическая проверка Claude Code блокирует как «Code from External». Нужно явное разрешение владельца.

`gary_pick.py`: вход `args.json` = `{"now": ISO со смещением, "state": {...}|null, "busy": bool}` → печатает `{"send", "chat_id", "image_url", "caption", "state"}`. Пул, вступления и строки про воду встроены в файл. `{"selftest": true}` печатает число упражнений и хэш данных.

`gary_reply.py`:
- режим `jev`: `{"mode":"jev","text","last"}` → `{"state","questions"}` для Jev, либо `{"shortcut":true,"answers"}` для текстов кнопок;
- режим `react`: `{"mode":"react","text","answers","state","events":[{"start","end"}],"now"}` → `{"reply","llm","llm_hint","key","state"}`. Библиотеку реплик качает с коммита `6c507d8`.

### 7.3 Агент-напоминалка
- **Модель:** `deepseek-v4.1-flash`
- **Инструменты:** `[googlecalendar, sandbox, telegram_bot]` (у нас `[3055, 3010, 3430]`)
- **input_schema:** `{"type":"object","properties":{}}`
- **Промпт** (писать на языке владельца, 5–6 предложений, как советует гайд FlyMyAI):

```
Ты Coach Gary, бот-напоминалка о разминке. 1) Найди в памяти (scope user) запись namespace coach_gary, key state; если её нет, state = null. 2) Проверь Google Calendar primary: идёт ли какое-то событие прямо сейчас (busy true/false). 3) В sandbox выполни Python: скачай https://raw.githubusercontent.com/Nrx838/railway-test/93867426a893278f6dcd27ea0cbeb08be8d102a2/gary_pick.py, запиши рядом args.json с {"now": текущее время America/New_York в ISO 8601 со смещением, "state": state, "busy": busy} и запусти скачанный файл, он напечатает JSON. 4) Если send=true: при непустом image_url отправь telegram_bot send_photo (photo=image_url, caption, parse_mode HTML), иначе send_message (text=caption, parse_mode HTML) в chat_id из JSON; текст не меняй. 5) Сохрани state из JSON в память: scope user, namespace coach_gary, key state.
```

**Тест:** `run_agent`, дождаться `get_run`. Удачный запуск сделал 9 вызовов инструментов: память → free/busy календаря → sandbox → `send_photo` → память. Сообщение пришло в Telegram.

### 7.4 Агент-ответчик
- **Модель:** `deepseek-v4.1-flash`
- **Инструменты:** `[googlecalendar, sandbox, telegram_bot, typesafe_jev]` (у нас `[3055, 3010, 3430, 3429]`)
- **Промпт:**

```
Ты ответчик Coach Gary в Telegram. 1) Возьми из памяти (scope user, namespace coach_gary) записи state и TELEGRAM_UPDATES_OFFSET. 2) Вызови telegram_bot get_updates с этим offset; если новых сообщений нет, сразу заверши работу. 3) Для каждого нового текстового сообщения из chat_id <CHAT_ID> по порядку: в sandbox скачай https://raw.githubusercontent.com/Nrx838/railway-test/93867426a893278f6dcd27ea0cbeb08be8d102a2/gary_reply.py, запиши рядом args.json {"mode":"jev","text":текст,"last":state.last} и запусти. Если в выводе shortcut=true, возьми оттуда answers; иначе вызови инструмент typesafe_jev decide со state и questions из вывода и возьми его answers. Затем возьми события Google Calendar primary за последние 3 часа и снова запусти тот же файл с {"mode":"react","text":текст,"answers":answers,"state":state,"events":[{"start","end"}],"now":текущее время America/New_York в ISO 8601}. Отправь send_message в <CHAT_ID> с текстом reply без изменений; только если llm=true, вместо reply напиши свой короткий ответ на сообщение пользователя по llm_hint. Для следующего сообщения используй state из вывода. 4) В конце сохрани в память (scope user, namespace coach_gary) state и TELEGRAM_UPDATES_OFFSET = update_id последнего сообщения + 1.
```

**Результаты тестов:**
- `✅ Done` → «👏 Oh. Didn't expect that. Respect.»: 11 вызовов, ~50 секунд.
- `phi` → Jev вернул `greeting` → «👋 Hey. Coach Gary here…». Этот запуск помечен failed, потому что в старом промпте было «вызови run_model», а внутри агента `run_model` получает 403.

### 7.5 Память
- **Scope `user`** — общий для обоих агентов. `task` виден только одному агенту, и ответчик не видит state напоминалки.
- **Ключи:** `coach_gary/state` (JSON состояния) и `coach_gary/TELEGRAM_UPDATES_OFFSET` (последний `update_id` + 1). Без offset бот будет отвечать на одни и те же сообщения повторно.

### 7.6 Кнопки: обходной путь
Коннектор `telegram_bot` **молча отбрасывает `reply_markup`** в `send_message` и `send_photo`. Поэтому:
- **inline-кнопки под каждым сообщением сделать нельзя**;
- **постоянную клавиатуру** внизу чата можно поставить **один раз** напрямую через Bot API. Она сохраняется:
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" -H 'Content-Type: application/json' -d '{"chat_id":<CHAT_ID>,"text":"🎺 Buttons are on.","reply_markup":{"keyboard":[[{"text":"✅ Done"},{"text":"💧 Drank water"}],[{"text":"📞 Was on a call"},{"text":"⏳ Later"}],[{"text":"😴 Too lazy"},{"text":"🙅 Skip"}]],"resize_keyboard":true,"is_persistent":true}}'
```
- Нажатие такой кнопки приходит обычным текстом. `gary_reply.py` узнаёт эти тексты и выдаёт ответ без вызова Jev (`shortcut`).

### 7.7 Заморозка и расписание
- **Заморозить и поставить на расписание одним вызовом:** `schedule_agent(execution_id=<удачный запуск>, cron_schedule, timezone="America/New_York")`. Создаётся компиляция с `instruction_md`, платформа сама пишет пошаговый пайплайн по удачному запуску.
- **Каждый вызов `schedule_agent` создаёт новую компиляцию.** Второе расписание для того же агента делается вторым вызовом. Уже замороженную компиляцию перенастраивают через `update_compilation`.
- **Снять расписание:** `update_compilation(compilation_id, cron_schedule="")`.
- **Замораживать только после удачного запуска с актуальным промптом:** инструкция компилируется из самого запуска.
- **Cron, который мы использовали:**
  - напоминалка: `0 10,13,16 * * 1-5` и `30 11,14,17 * * 1-5`;
  - ответчик раз в 3 минуты в течение получаса после каждого слота: `1-30/3 10,13,16 * * 1-5` и `31-59/3 11,14,17 * * 1-5`.

### 7.8 Почему выключили: цена
Баланс падал на **$0.15–0.25 за запуск**. Это оценка по изменению баланса: цена отдельного запуска у API вернула 404. Причины:
- на каждом шаге LLM заново читает инструкцию и схемы инструментов;
- платформа проверяет результат ещё одним вызовом LLM («completion review»);
- sandbox и память вызываются как отдельные инструменты.

| Сценарий | В месяц на 1 пользователя |
|---|---|
| Ответчик каждые 5 минут + напоминания | ~$100+ |
| Только по событию (если бы был триггер) + нынешние агенты | ~$50 |
| Урезанный замороженный агент (оценка) | ~$3–8 |
| Функция-код без LLM + Jev | ~$0.01 |

Все расписания сняты: компиляции 370 и 371, плюс по просьбе владельца чужая Slack-сводка 315. Чтобы вернуть её: cron `0 8 * * 1-5`, UTC.

### 7.9 Если собирать на агентах снова
1. **Сделать промпт короче**, оставить минимум инструментов, заморозить и мерить цену `get_execution_price`.
2. **Опрашивать реже:** окно в 30 минут после слота, а не весь день.
3. **Отвечать на кнопки без LLM,** как только у платформы появятся код-функции и триггеры (§10).

---

## 8. Вариант B: бэкенд на Fly.io + Jev через FlyMyAI (рабочий)

Бэкенд — **одна маленькая машина Fly.io** (`shared-cpu-1x`, 256 MB, регион `iad`, ~$1.94/мес) и **диск на 1 ГБ** под SQLite (~$0.15/мес). HTTP-сервис не нужен: бот сам опрашивает Telegram, поэтому машина постоянно включена и отвечает на нажатия мгновенно. Модель вызывается только для свободного текста, через API FlyMyAI (Jev).

```
Telegram ⇄ Fly.io machine: bot.py (python-telegram-bot 21.6, long polling, JobQueue раз в 30 с)
              ├─ coach.py      чистая логика: слоты, выбор упражнения, реакции, отчёт
              ├─ reactions.json / exercises.json
              ├─ SQLite на томе Fly.io /data/gary.db (users: chat_id, tz, state, name; meta: jev_calls, jev_usd)
              └─ Jev → FlyMyAI REST только для свободного текста
```

### Файлы (`bot/`)
- `bot.py` — хэндлеры, клавиатуры, планировщик, вызов Jev;
- `coach.py` — логика без Telegram и сети, покрыта симуляцией недели;
- `reactions.json`, `exercises.json` — контент;
- `requirements.txt`: `python-telegram-bot[job-queue]==21.6`, `httpx>=0.27`, `tzdata`;
- `Dockerfile`, `fly.toml`, `deploy-fly.sh` — бэкенд на Fly.io;
- `.env.example`, `run.sh` — локальный запуск для разработки.

### Переменные окружения
`TELEGRAM_TOKEN` (обязательно), `FLYMYAI_API_KEY` (для Jev), `DB_PATH` (на Fly.io `/data/gary.db`, задаётся в `fly.toml`). На Fly.io первые два хранятся как **secrets**, а не в образе.

### Локальный запуск (разработка)
```bash
cd bot && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
```bash
cp bot/.env.example bot/.env    # вписать токен и ключ
```
```bash
bot/run.sh
```

### Деплой на Fly.io
```toml
# fly.toml
app = "coach-carter-bot"
primary_region = "iad"
[env]
  DB_PATH = "/data/gary.db"
[[mounts]]
  source = "gary_data"
  destination = "/data"
[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```
```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py coach.py exercises.json reactions.json ./
CMD ["python", "bot.py"]
```
Одной командой, всё делает скрипт `deploy-fly.sh`:
```bash
curl -L https://fly.io/install.sh | sh
```
```bash
cd bot && ./deploy-fly.sh coach-carter-bot
```
Что делает скрипт:
1. Проверяет `flyctl` и вход в аккаунт (если не вошёл, открывает `fly auth login`).
2. Останавливает локального бота: Telegram отдаёт обновления только одному опрашивающему процессу.
3. Прописывает имя приложения в `fly.toml` и создаёт приложение.
4. Создаёт том `gary_data` на 1 ГБ в регионе `iad`.
5. Переносит `TELEGRAM_TOKEN` и `FLYMYAI_API_KEY` из `.env` в **Fly secrets** (`fly secrets import`). Токены не попадают ни в образ, ни в git.
6. Делает `fly deploy --ha=false` и `fly scale count 1`: ровно одна машина, иначе два процесса будут опрашивать один токен.

После деплоя:
- логи: `fly logs -a coach-carter-bot`;
- статус: `fly status -a coach-carter-bot`;
- обновить код: `fly deploy -a coach-carter-bot`;
- база переживает перезапуски и деплои, потому что лежит на томе.

Образ собирается и проверен локально: внутри импортируются `coach` и `telegram`, в пуле 65 упражнений.

### Проверено
- **Симуляция рабочей недели:** 30 напоминаний, подряд ни одного повтора, все подписи меньше 1024 символов.
- **Правильные категории** на боль, паузу, созвон, грубость и `+`/`-`.
- **В живом Telegram:**
  - кнопки под сообщением;
  - выбор города;
  - `/stretch`;
  - свободный текст через Jev;
  - `/cost`.

---

## 9. Грабли и обходные пути

| Проблема | Что происходит | Решение |
|---|---|---|
| `run_model` внутри агента | HTTP 403 на любую модель (Jev, nano-banana) | Jev через инструмент `typesafe_jev.decide`, картинки через REST |
| `run_model` через MCP для картинок | возвращает `read_handle`, `download_file` отвечает «invalid for this MCP principal» | REST `.../gpt-image-2-5/predict` с API-ключом |
| Агент без подходящего инструмента | DeepSeek-агент «пытается изо всех сил»: веб-поиск, облачный браузер, десятки шагов | `cancel_run`, чёткий промпт, только нужные инструменты |
| `telegram_bot` | отбрасывает `reply_markup` | постоянная клавиатура через Bot API один раз; inline-кнопки только в своём боте |
| Приём сообщений | нет триггера на входящее, только `get_updates` по cron | опрос в окне после напоминаний или свой бот |
| Память | `task` scope не виден другому агенту | `scope user` |
| ID коннектора | меняется после переподключения | заново `list_configured_tools` |
| Код в агенте | `code-blocks` не подключить, большой параметр падает | код в GitHub по ссылке на коммит + sandbox |
| Sandbox | каждый вызов в чистом окружении, файлы не сохраняются | скачивание и запуск в одном вызове |
| Jev REST | ответ SSE, а не JSON | парсить строки `data:` |
| GPT Image размеры | только `1024x1024`, `1536x1024`, `1024x1536`, `auto` (иначе 422) | генерировать 1536×1024 и обрезать до 16:9 |
| ElevenLabs TTS | по умолчанию `eleven_multilingual_v2` | всегда явно `model_id: eleven_v3` |
| Произношение | «FlyMyAI» → «Fly.ai», «Jev» → «Jebb/Javen» | писать фонетически: `Fly My A.I.`, `Jehv...` и проверять через `speech_to_text` |
| fal из FlyMyAI | коннектор `fal_ai` умеет только искать модели, цены и статус очереди; `fal_api` не подключён | музыка через Suno или Gemini, либо свой ключ fal |
| Запуск кода с GitHub | блокируется проверкой безопасности Claude Code | явное разрешение владельца, ссылка на коммит |

---

## 10. Чего не хватает FlyMyAI

1. **Webhook-триггер для агента:** URL, который сразу отвечает 200, проверяет секрет и запускает обработку асинхронно. Нужен для Telegram, форм, вебхуков.
2. **Лёгкие функции без LLM:** выполнить код за секунду и за доли цента, модели вызывать из кода. **Самое важное:** без этого триггер просто быстрее тратит деньги.
3. **Секреты для кода**, чтобы функция вызывала сторонние API без передачи токена через модель.
4. **Полный Telegram-коннектор:** `reply_markup`, `answerCallbackQuery`, `editMessageReplyMarkup`.
5. **KV-хранилище или маленькая БД** для состояния многих пользователей.
6. **`run_model` внутри агентов** (сейчас 403) и **скачивание результата `run_model` через MCP**.
7. **Цена одного запуска** через API (у нас `get_execution_price` вернул 404).

Для сравнения: у Vetta / Naïve (vetta.sh, usenaive.ai) есть **Apps** (хостинг приложений с Postgres), cron, «спящие» агенты, которые ничего не стоят в простое, и дешёвые «completion windows». Пробуждение агента входящим событием у них тоже пока в статусе «coming soon».

---

## 11. Медиа через FlyMyAI

### Озвучка (ElevenLabs)
```
execute_tool(tool="elevenlabs", action="text_to_speech",
  arguments={"text": "...", "voice_id": "nPczCjzI2devNBz1zQrb", "model_id": "eleven_v3", "output_format": "mp3_44100_128"})
→ result.agent_file.public_url, duration_seconds
```
- **Голос** Brian (`nPczCjzI2devNBz1zQrb`), модель `eleven_v3` понимает теги вроде `[deadpan]`.
- **Проверка:** `elevenlabs.speech_to_text` на `cloud_storage_url` дубля. Так видно, не прочитался ли тег вслух и как звучат названия.

### Звуковые эффекты
`elevenlabs.generate_sound_effect` с параметрами `text`, `duration_seconds` (0.5–30), `prompt_influence`. Сделано 15 штук: свисток, дверь, «бип», монетка, level up, «бульк», курсор, выбор, штамп, фейерверк, вжух, уведомление, клик, тревога, шестерёнки.

### Картинки (GPT Image 2.5) через REST
Скрипт `my-video/scripts/flymy-image.py`:
```bash
FLYMYAI_API_KEY=... python3 scripts/flymy-image.py out.png "prompt" 1536x1024 transparent high
```
- `POST https://api.flymy.ai/api/v1/flymyai/gpt-image-2-5/predict`, multipart: `prompt`, `size`, `quality` (low / medium / high), `background` (`transparent` для спрайтов).
- Ответ SSE, картинка в `output_data.image[0]`: base64 или URL.
- **Персонажи листом поз в одной генерации** («ONE character in a 4 by 2 grid of 8 poses, identical design…, transparent background, no text») — единственный надёжный способ получить одинакового персонажа во всех позах.
- **Нарезка:** `scripts/slice-sheet.py SHEET.png 4 2 OUT name1…name8`. Прозрачность ≥128 делается полной, иначе нулевой: так срезается мягкое свечение. Мелкие фрагменты у края ячейки выбрасываются.

### Музыка
Лучшие модели на fal сейчас такие (цены из `FAL_AI_GET_PRICING`):
- `elevenlabs/music/v2.5`: $0.60/мин, точная длина и план из секций;
- `google/lyria-3.5`: $0.10 за генерацию;
- `minimax/music-3`: $0.002/с;
- Stable Audio 3: ~$0.04.

Запустить их из FlyMyAI нельзя (§9). В итоге трек сделали в Gemini по промпту с таймкодами под сцены, и таймкоды совпали: дроп на 0:28, финал на 1:06.

---

## 12. Промо-ролик и обложка

- **Remotion** обновлён до 4.0.529. Композиция `CoachCarterPromo` лежит в `my-video/src/CoachCarter/`: `constants.ts`, `pixel.tsx` (компоненты), `scenes1.tsx`, `scenes2.tsx`, `index.tsx`.
- **Параметры:** 2226 кадров = 74.2 с, 1920×1080, 30 fps.
- **Структура:** цена → стек в виде экрана выбора команды RPG → PRESS START → Кевин превращается в креветку → входит Картер → Telegram с кнопками → LEVEL UP → отчёт → Jev и штамп «~300× cheaper» → «FlyMyAI — infrastructure for AI agents».
- **Звук:**
  - музыка приглушается под голосом (0.37 → 0.13);
  - эффекты идут с общим множителем 0.35;
  - итог −13.9 LUFS, пик −0.9 dB, нормализация `ffmpeg loudnorm=I=-14:TP=-1`.
- **Рендер:**
```bash
cd my-video && npx remotion render src/index.ts CoachCarterPromo out/coach-carter.mp4 --concurrency=50%
```
- **Кадры для проверки:** `node scripts/stills.mjs CoachCarterPromo <dir> 0.5 <кадры…>`.
- **Обложка:** композиция `CoachCarterThumb` = картинка GPT Image 2.0 плюс логотипы FlyMy.AI, Telegram, Fly.io, GPT Image и «JEV by TypeSafe AI». Файл `out/coach-carter-cover.jpg`.
- **Полный сценарий:** `/home/nrx83/AI/remotion/coach-carter-video-final.md`.

---

## 13. Цены

| Что | Цена |
|---|---|
| Jev, один разбор ответа | $0.00003 (измерено) |
| Нажатие кнопки / `+` / `-` | $0 (модель не вызывается) |
| AI-счёт за месяц, 10 текстовых ответов в день | < $0.01 |
| Большая LLM за ответ (Claude Opus 5, ~1.5k вход / 80 выход) | ≈ $0.0095, то есть «~300× дороже» (оценка) |
| Бэкенд Fly.io: shared-cpu-1x 256MB | $1.94/мес (+ диск 1 ГБ ~$0.15) |
| Агент FlyMyAI, один запуск | ~$0.15–0.25 (оценка по балансу) |
| GPT Image 2.5, одна картинка | $0.08 |
| Весь проект в FlyMyAI: тесты агентов, озвучка, картинки, эффекты | ~$5.9 (баланс $81.94 → $76.03) |

**Модели для агентов** из `list_agent_models`, цена за 1M токенов, вход / выход:
- DeepSeek V4.1 Flash $0.30 / $1.20;
- MiMo V2.5 $0.14 / $0.28;
- GLM 5.3 Flash $0.15 / $0.50;
- Gemini 3.8 Flash $0.75 / $3.75;
- Claude Sonnet 5 $2 / $10;
- Claude Opus 5.5 $4 / $20;
- GPT-6 Luna $0.10 / $0.50.

---

## 14. Приложение: ID и ссылки этого аккаунта

Это ID аккаунта `Alexander_nrx83`. При сборке у себя они будут другими.

| Объект | ID |
|---|---|
| Коннектор `telegram_bot` | 3430 (public `c5594224-4509-40f1-978c-f143169d553b`) |
| Коннектор `googlecalendar` | 3055 |
| Коннектор `sandbox` | 3010 |
| Коннектор `typesafe_jev` | 3429 |
| Агент-напоминалка | `efce8940-0093-4020-9339-15306041abad` (удачный запуск `urc-httj-cya`) |
| Агент-ответчик | `f71fdc25-07b9-4a69-a5a9-71acdc469fc6` (удачный запуск `jos-zadm-gvd`; компиляции 370, 371, расписание снято) |
| Агент для картинок (не заработал, 403) | `2463d810-9270-493c-9403-913a21fc63f3` |
| Telegram-бот | `@CoachCarter83_bot` |
| GitHub | `Nrx838/railway-test`, ветка `coach-gary`: `b006455` → `6c507d8` → `9386742` → `f6e9851` → `26b8bf0` → `8d0db60` |

### Чек-лист «собрать заново»
1. Бот в @BotFather → токен.
2. Ключ API FlyMyAI (app.flymy.ai/profile).
3. `git clone -b coach-gary https://github.com/Nrx838/railway-test` → папка `bot/`.
4. `.env` с `TELEGRAM_TOKEN` и `FLYMYAI_API_KEY`. По желанию сначала `run.sh` локально: проверить `/start`, `/stretch`, кнопки, свободный текст, `/cost`.
5. Бэкенд на Fly.io: установить `flyctl` и запустить `./deploy-fly.sh` (§8). Скрипт сам остановит локальную копию.
6. Для варианта на агентах: коннекторы (§7.1) → агенты с промптами из §7.3–7.4 (подставить свой `chat_id`) → тестовые запуски → `schedule_agent`. Следить за балансом.
