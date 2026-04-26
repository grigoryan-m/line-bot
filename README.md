# LINE Bot — порт Telegram-бота

## Структура проекта

```
line_bot/
├── main.py                  # FastAPI webhook — точка входа
├── config.py                # Переменные окружения
├── requirements.txt
├── .env.example
│
├── handlers/
│   ├── start.py             # /start, выбор языка, главное меню
│   ├── loyalty.py           # Регистрация карты лояльности (FSM)
│   ├── stores.py            # Поиск магазинов по гео / региону
│   ├── manager.py           # AI-чат + эскалация на менеджера
│   ├── about.py             # О компании
│   └── socials.py           # Соцсети
│
├── utils/
│   ├── line_api.py          # LINE Messaging API хелперы
│   ├── user_data.py         # FSM состояния пользователей (in-memory)
│   ├── ai.py                # Claude AI (Anthropic)
│   ├── otp.py               # Генерация и верификация OTP
│   ├── odoo.py              # Регистрация в Odoo CRM
│   ├── stores.py            # Поиск магазинов
│   └── analytics.py        # Аналитика
│
├── locales/
│   └── texts.py             # Тексты на EN / RU / TH
│
└── data/
    └── stores.json          # База магазинов
```

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env
# заполни .env своими ключами
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Соответствие функций Telegram → LINE

| Telegram | LINE |
|---|---|
| InlineKeyboardMarkup | Flex Message (главное меню) |
| Quick Reply кнопки | Quick Reply (да/нет, регион, язык) |
| ReplyKeyboard (геолокация) | Quick Reply с location action |
| Callback query | Postback event |
| FSM (aiogram) | user_data.py (in-memory state) |
| answer_photo | push_image (LINE image message) |

## Особенности LINE vs Telegram

- **Режим standby** — бот использует `push` вместо `reply` (см. main.py)
- **Кнопки** — в LINE нет обычных inline-кнопок как в TG; используются:
  - **Quick Reply** — кнопки под полем ввода (до 13 шт)
  - **Flex Message** — для главного меню (карточка с кнопками)
  - **Button Template** — для простых карточек с до 4 кнопками
- **Геолокация** — запрашивается через Quick Reply с `type: location`
- **Follow event** — аналог `/start` в Telegram, срабатывает при добавлении бота

## Настройки в LINE Developers Console

1. `Webhooks` → **ON**
2. `Auto-reply messages` → **Disabled**
3. `Greeting messages` → **Disabled**
4. `Chat` toggle → **OFF** (иначе mode будет `standby`)
