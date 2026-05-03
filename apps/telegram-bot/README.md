# apps/telegram-bot — Telegram Bot Gateway

## Назначение

Отдельное приложение на **aiogram 3.x** для Telegram forum group.

MVP TG-01:
- polling mode для dev
- чтение `chat_id`, `message_thread_id`, `user_id`, `username`, `text`
- ответы в тот же topic через `message_thread_id`
- команды `/start`, `/help`, `/projects`, `/agents`, `/tasks`
- интеграция с backend API для списков и создания task

## Что НЕ делает TG-01

- не запускает runtime/агентов напрямую
- не использует webhook (структура заложена, но не включена)
- не делает deploy

## Структура

```text
apps/telegram-bot/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── bot.py
│   ├── handlers/
│   │   ├── start.py
│   │   ├── commands.py
│   │   └── messages.py
│   ├── services/
│   │   ├── api_client.py
│   │   └── topic_context.py
│   └── keyboards/
└── tests/
```

## Запуск (после отдельного approve)

```bash
python -m app.main
```

> Для текущего этапа запуск polling не выполняется автоматически.
