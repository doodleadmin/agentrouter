# Telegram Flow — Маршрутизация сообщений

Версия: 1.0
Дата: 2026-05-03

## Обзор

Telegram forum group — основной интерфейс управления. Каждое сообщение маршрутизируется через topic → agent/project → task → execution.

## Структура группы

Telegram supergroup с включённым режимом **Topics / Forum**.

### Рекомендуемые топики

| Topic | Kind | Привязка | Назначение |
|-------|------|----------|------------|
| General | `general` | — | Общий чат, координация, статусы |
| Agent: Backend | `agent` | backend-agent | Задачи backend-агенту |
| Agent: Frontend | `agent` | frontend-agent | Задачи frontend-агенту |
| Agent: DevOps | `agent` | devops-agent | Задачи devops-агенту |
| Project: academy-bot | `project` | academy-bot | Все задачи по проекту |
| Approvals | `approvals` | — | Запросы на подтверждение |
| System Logs | `system` | — | Логи задач, ошибок, деплоев |

### Подход: гибридный

```
General → Orchestrator решает, куда направить
Agent:* → Сообщение напрямую агенту (указать проект в тексте)
Project:* → Сообщение в контексте проекта (Orchestrator выбирает агента)
Approvals → Автоматические запросы подтверждений
System Logs → Автоматические логи
```

## Входящие данные

Каждое сообщение содержит:

```python
class TelegramMessage:
    chat_id: int              # ID группы
    message_thread_id: int    # ID топика (None для General)
    user_id: int              # ID пользователя
    text: str                 # Текст сообщения
    reply_to_message: Optional[Message]  # Ответ на другое сообщение
    attachments: List[Attachment]        # Файлы, фото
```

## Алгоритм маршрутизации

```python
async def route_message(message: TelegramMessage) -> Task:
    # 1. Определить topic
    topic = await db.topics.get_by_chat_and_thread(
        chat_id=message.chat_id,
        thread_id=message.message_thread_id
    )

    # 2. Маршрутизация по kind
    if topic.kind == "agent":
        agent = await db.agents.get(topic.agent_id)
        project = await detect_project(message.text)
        return await create_task(agent, project, message)

    if topic.kind == "project":
        project = await db.projects.get(topic.project_id)
        agent = await detect_agent(message.text, project)
        return await create_task(agent, project, message)

    if topic.kind == "general":
        intent = await classify_intent(message.text)
        project = await detect_project(message.text)
        agent = await select_agent(intent, project)
        return await create_task(agent, project, message)

    if topic.kind == "approvals":
        return await handle_approval_response(message)

    if topic.kind == "system":
        return None
```

## Команды

### `/bind_topic`
```
/bind_topic agent backend
/bind_topic project academy-bot
/bind_topic general
/bind_topic approvals
/bind_topic system
```

### `/projects`
```
/projects                                          — список
/new_project slug=academy-bot repo=/opt/repos/...  — создать
```

### `/agents`
```
/agents                                            — список
/agent backend project=academy-bot task="..."      — вызвать
```

### `/task`
```
/tasks                                             — список активных
/task <id>                                         — статус задачи
/task <id> approve                                 — одобрить
/task <id> reject                                  — отклонить
/task <id> cancel                                  — отменить
```

### `/plan`
```
/plan project=academy-bot agent=backend добавь webhook status endpoint
```

### `/run`
```
/run task=task-0001
```

### `/memory`
```
/memory search project=academy-bot query="как деплоить staging"
/memory append project=academy-bot file=agent-notes.md text="..."
```

### `/deploy`
```
/deploy project=academy-bot env=staging branch=agent/task-0001
/deploy project=academy-bot env=production branch=main   → требует approval
```

## Approval Cards

```
┌────────────────────────────────────────┐
│ ⚠️ Approval Request                    │
│                                        │
│ Task: task-0001                        │
│ Project: academy-bot                   │
│ Agent: backend                         │
│ Risk: high                             │
│ Action: code_change                    │
│                                        │
│ Plan:                                  │
│ 1. Добавить /health endpoint           │
│ 2. Добавить тест                       │
│ 3. Обновить API docs                   │
│                                        │
│ Files: app/routes/health.py, tests/... │
│                                        │
│ [✅ Approve]  [❌ Reject]  [📋 Diff]   │
└────────────────────────────────────────┘
```

## Webhook vs Long Polling

- **Production:** webhook (быстрый отклик, HTTPS)
- **Development:** long polling (проще, не нужен HTTPS)
