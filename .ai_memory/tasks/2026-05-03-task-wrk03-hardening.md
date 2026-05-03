# Task Summary: WRK-03-hardening — Security Hardening

**Дата:** 2026-05-03  
**Агент:** backend-architect  
**Статус:** ✅ Выполнена

---

## Цель

Закрыть CRITICAL/HIGH vulnerabilities из post-implementation security review WRK-03 перед этапами fake E2E / DockerSandboxRunner / real execution.

## Закрытые issues

### CRITICAL
| ID | Описание | Решение |
|----|----------|---------|
| C-1 | shell escape через `sh -c`/`bash -c`/`python -c`/`powershell` | Добавлены в denylist |
| C-2 | chaining через `&&`/`;`/`\|`/`\|\|`/backticks/`$()` | Добавлены в denylist |
| C-3 | unbounded `event_type` в API | `ALLOWED_EVENT_TYPES` frozenset + `field_validator` |

### HIGH
| ID | Описание | Решение |
|----|----------|---------|
| H-1 | `curl`/`wget`/`nc`/`telnet`/`ftp`/`scp`/`rsync` | Добавлены в denylist |
| H-2 | `sudo`/`su`/`chmod`/`chown` | Добавлены в denylist |

### Дополнительно закрыты (из medium review)
| ID | Описание |
|----|----------|
| M-3 | `git checkout`/`git clone`/`git fetch`/`git pull`/`git push`/`git merge`/`git rebase`/`git commit` |
| M-4 | Generic `python -m` больше не разрешён — только точные safe patterns |

## Что изменено

### command_policy.py
- `DENY_PATTERNS` расширен с ~20 до ~55 patterns
- `ALLOW_PREFIXES` сокращён до 9 точных паттернов
- Denylist всегда проверяется первым (приоритет)

### schemas/task_event.py
- Добавлен `ALLOWED_EVENT_TYPES: frozenset[str]` (21 разрешённый тип)
- `TaskEventCreate.event_type` валидируется через `field_validator`

### Тесты
- `apps/worker/tests/test_execute_security.py` — 44 теста (6 allowlist + 38 bypass)
- `apps/api/tests/test_event_type_validation.py` — 2 теста (reject invalid + accept valid)

## Проверки

| Компонент | ruff | pytest |
|-----------|------|--------|
| API | ✅ | ✅ 149/149 |
| Worker | ✅ | ✅ 73/73 |

## Ограничения соблюдены
- ❌ Не запускался Docker
- ❌ Не запускались shell-команды
- ❌ Не делался deploy
- ❌ Не запускались миграции
- ❌ Не менялся .env/secrets
- ❌ Не подключался к production/staging

## Следующие шаги
- WRK-04: Real sandbox execution (approval-gated)
