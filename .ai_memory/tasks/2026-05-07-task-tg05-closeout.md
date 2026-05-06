# TG-05 Closeout: Live Telegram Approval Flow

**Date:** 2026-05-07
**Final Verdict:** ✅ **PASS**

---

## 1. Confirmed Capabilities

| Capability | Status | Evidence |
|------------|--------|----------|
| Worker reads TELEGRAM_BOT_TOKEN from .env.local process-scoped | ✅ | start-worker.sh sources .env.local, logs `***set***` |
| Worker uses TelegramNotifier when token exists | ✅ | Phase 2: no StubNotifier in log |
| Real Telegram notification delivery | ✅ | Phase 2/3/4: sendMessage 200 OK |
| Low-risk task notification | ✅ | Phase 2: task-0001 approved, notification delivered |
| Medium-risk task creates waiting_approval | ✅ | Phase 3: task-0003, Phase 4: task-0004 |
| Admin /approve works | ✅ | Phase 3: task-0003 approved |
| Admin /reject works with reason | ✅ | Phase 4: task-0004 cancelled, reason saved |
| Non-admin approval/reject blocked | ✅ | Unit tests 8/8 each (fail-closed) |
| Feedback loop does not occur | ✅ | Phase 2: 1 task, Phase 3: 3 tasks, Phase 4: 4 tasks |
| Secret values never printed | ✅ | All logs show `***set***` or `(set, not displayed)` |
| .env.local never committed | ✅ | .gitignore covers it |

---

## 2. Live Evidence

### Phase 2 — Notification Delivery
- Task `f6972b69` (task-0001): low-risk → approved
- Worker log: `POST https://api.telegram.org/bot.../sendMessage "HTTP/1.1 200 OK"`
- method = `telegram` (not stub)
- message_id = 56, delivered to chat 1113930428

### Phase 3 — Admin Approve
- Task `0e8f0597` (task-0003): medium-risk → waiting_approval
- Approval `351e4221`: pending → approved
- approved_by: 1113930428
- Event: approval_granted
- Task final: approved

### Phase 4 — Admin Reject
- Task `db6f1f72` (task-0004): medium-risk → waiting_approval
- Approval `bee793b6`: pending → rejected
- approved_by: 1113930428
- reason: "reason: TG-05 reject smoke test"
- Event: approval_rejected
- Task final: cancelled

---

## 3. Bugs Found & Fixed During TG-05

### Bug 1: Router Ordering (bot.py)
- **Problem:** `messages_router` catch-all consumed `/approve` and `/reject` before command routers.
- **Fix:** Moved approve_router, reject_router, status_router, plan_router BEFORE messages_router in bot.py.
- **Commit:** `02bc57b fix(telegram): route approval commands before catch-all`

### Bug 2: Approval Task Transition (approvals.py)
- **Problem:** `approval_service.approve()` updated approval status but didn't transition task status.
- **Fix:** Added task status transition in approvals router (waiting_approval → approved on approve, waiting_approval → cancelled on reject).
- **Commit:** `02bc57b fix(telegram): route approval commands before catch-all`

---

## 4. Known Non-Blocking Finding

**BUTTON_DATA_INVALID** — cosmetic error in bot logs when sending inline keyboard after /approve or /reject.

- **Impact:** None — command-based flows work correctly.
- **Root cause:** Inline callback data format may exceed Telegram's 64-byte limit or have invalid characters.
- **Recommendation:** Separate task — `TG-06` or `TG-COSMETIC-01`: fix inline callback button data length/format.

---

## 5. Security Summary

| Check | Status |
|-------|--------|
| TELEGRAM_ADMIN_USER_IDS fail-closed | ✅ |
| Empty admin list rejects everyone | ✅ |
| Non-admin does not call API | ✅ |
| Token not logged | ✅ |
| SecretRedactionFilter active | ✅ |
| .env.local gitignored | ✅ |

---

## 6. Operational Notes

- Real live flows should run from Ubuntu/WSL2.
- Windows PowerShell runtime scripts are legacy.
- Linux scripts (`scripts/dev-linux/`) are canonical for local runtime validation.

---

## 7. Commits

| Hash | Message |
|------|---------|
| `342443a` | feat(telegram): add live notification env and admin approval gate |
| `288d3e1` | docs(telegram): record TG-05 live notification smoke |
| `02bc57b` | fix(telegram): route approval commands before catch-all |
| `c67ad72` | docs(telegram): record TG-05 admin reject flow |

---

## 8. Final Verdict

## **TG-05: PASS** ✅

All 6 objectives confirmed:
1. ✅ Live Telegram notification delivery
2. ✅ Live admin approve flow
3. ✅ Live admin reject flow
4. ✅ Admin gate fail-closed
5. ✅ No feedback loop
6. ✅ Worker uses TelegramNotifier when TELEGRAM_BOT_TOKEN is present
