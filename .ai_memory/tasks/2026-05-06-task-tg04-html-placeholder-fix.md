---
date: 2026-05-06
task_id: tg04-html-placeholder-fix
status: completed
agent: studio-orchestrator
---

# TG-04: HTML Placeholder Fix — TelegramBadRequest

## Problem
Bot has global `parse_mode=HTML` (via `DefaultBotProperties`). Help text contained raw angle-bracket placeholders like `<project_slug>`, `<agent_slug>`, `<task_id|external_id>` which Telegram's HTML parser treated as invalid HTML tags, causing `TelegramBadRequest: can't parse entities: Unsupported start tag "project_slug"`.

## Root Cause
6 handler files had raw `<placeholder>` syntax in user-facing messages. Additionally, some dynamic values from API responses (action names, user-provided reason text) were not HTML-escaped before insertion into HTML-formatted messages.

## Files Changed (6 handler files + 1 test)

### Placeholder fixes (raw `<slug>` → `<code>slug</code>`):
| File | Line | Before | After |
|------|------|--------|-------|
| `messages.py:45` | help text | `<project_slug>` | `<code>project_slug</code>` |
| `bind_topic.py:21` | format hint | `<project_slug>` | `<code>project_slug</code>` |
| `plan_handler.py:19` | usage | `<task_id\|external_id>` | `<code>task_id</code> or <code>external_id</code>` |
| `approve_handler.py:19` | usage | `<task_id\|external_id>` | `<code>task_id</code> or <code>external_id</code>` |
| `reject_handler.py:19` | usage | `<task_id\|external_id>` | `<code>task_id</code> or <code>external_id</code>` |
| `status_handler.py:19` | usage | `<task_id\|external_id>` | `<code>task_id</code> or <code>external_id</code>` |

### Dynamic value escaping (added `from html import escape as html_escape`):
| File | What escaped |
|------|-------------|
| `approve_handler.py:68` | `result.get('action')` → `html_escape(str(result.get('action', 'unknown')))` |
| `reject_handler.py:71` | `result.get('action')` + `reason` → both html_escaped |
| `bind_topic.py:28,33` | `parsed.project_slug`, `parsed.agent_slug` in error messages |
| `bind_topic.py:63-64` | `parsed.project_slug`, `parsed.agent_slug` in success message |
| `messages.py:68-72` | `task.get('external_id')`, `topic_ctx.title`, `username` |

### Import order fix (ruff I001):
- `approve_handler.py`, `reject_handler.py`, `bind_topic.py`: moved `from html import escape as html_escape` before aiogram imports (stdlib before third-party)

### Test update:
- `test_messages.py:62`: assertion updated from raw `<project_slug>` to `<code>project_slug</code>`

## Validation
- `python -m compileall app` ✅
- `ruff check app` ✅ (All checks passed)
- `pytest tests -v` ✅ (64/64 passed)
- `.env.local` gitignored ✅

## Decision: `<code>slug</code>` over `&lt;slug&gt;`
Used `<code>slug</code>` because it renders as monospace in Telegram (standard for command args) and is more readable than HTML-entity escaped angle brackets.

## Security
- No secrets touched
- No .env files modified
- Dynamic values from API/user now properly escaped via `html.escape()`
- formatters.py `_escape_html()` was already safe; this fix extends coverage to handler-level dynamic values
