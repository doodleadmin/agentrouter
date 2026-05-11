# Local Runner API Contract (Draft, DEV-12A)

> Draft contract only. Not implemented in DEV-12A.

## Auth assumptions

- Runner authenticates via pairing token/session.
- User-facing API uses existing auth/session model.
- Sensitive operations require explicit approval linkage.

---

## Runner pairing

### `POST /runners/pairing/start`
- **Purpose:** Start pairing flow and return short-lived pairing challenge.
- **Request:** `{ "device_name": "...", "platform": "windows|mac|linux" }`
- **Response:** `{ "pairing_id": "...", "pairing_code": "...", "expires_at": "..." }`
- **Auth:** user session
- **Approval:** none
- **Safety:** code expires quickly; rate limit attempts.

### `POST /runners/register`
- **Purpose:** Complete registration after pairing verification.
- **Request:** `{ "pairing_id": "...", "pairing_code": "...", "allowed_root": "F:\\dev", "capabilities": [...] }`
- **Response:** `{ "runner_id": "...", "status": "online|pairing", "token": "..." }`
- **Auth:** pairing challenge
- **Approval:** none
- **Safety:** validate/normalize root on registration.

### `POST /runners/revoke`
- **Purpose:** Revoke runner access.
- **Request:** `{ "runner_id": "...", "reason": "..." }`
- **Response:** `{ "ok": true }`
- **Auth:** user session
- **Approval:** recommended for shared workspaces
- **Safety:** invalidates runner token immediately.

---

## Runner heartbeat

### `POST /runners/{runner_id}/heartbeat`
- **Purpose:** Runner liveness + status refresh.
- **Request:** `{ "status": "online", "capabilities": [...], "timestamp": "..." }`
- **Response:** `{ "ok": true, "server_time": "..." }`
- **Auth:** runner token
- **Approval:** none
- **Safety:** heartbeat does not grant additional permissions.

### `GET /runners`
- **Purpose:** List registered runners.
- **Response:** array of runner summary objects.
- **Auth:** user session
- **Approval:** none

### `GET /runners/{runner_id}`
- **Purpose:** Runner details/status.
- **Response:** runner detail object.
- **Auth:** user session
- **Approval:** none

---

## Runner jobs

### `GET /runners/{runner_id}/jobs/next`
- **Purpose:** Runner pulls next job (polling mode).
- **Response:** `{ "job": {...} | null }`
- **Auth:** runner token
- **Approval:** depends on job kind
- **Safety:** server sends only jobs scoped to runner root/workspace.

### `POST /runners/{runner_id}/jobs/{job_id}/result`
- **Purpose:** Submit job result.
- **Request:** `{ "status": "completed|failed", "stdout": "...redacted...", "stderr": "...redacted...", "files_changed": [...] }`
- **Response:** `{ "ok": true }`
- **Auth:** runner token
- **Approval:** none
- **Safety:** server side redaction validation.

---

## Workspace source

### `GET /workspaces`
- **Purpose:** List workspace sources and states.

### `POST /workspaces`
- **Purpose:** Create workspace source selection.

### `PATCH /workspaces/{workspace_id}`
- **Purpose:** Update workspace source state/project selection.

### `GET /workspaces/{workspace_id}/projects`
- **Purpose:** List discovered project folders from runner.

**Auth:** user session for all.
**Approval:** none for read/select actions.
**Safety:** enforce allowed root boundary.

---

## File operations

### `POST /workspaces/{workspace_id}/files/tree`
- Purpose: list directory tree (scoped)

### `POST /workspaces/{workspace_id}/files/read`
- Purpose: read file (policy-filtered)

### `POST /workspaces/{workspace_id}/files/search`
- Purpose: scoped text search

### `POST /workspaces/{workspace_id}/files/propose-patch`
- Purpose: generate patch/diff proposal only

### `POST /workspaces/{workspace_id}/files/apply-patch`
- Purpose: apply patch
- **Status:** FUTURE, approval-gated

**Auth:** user session + runner linkage
**Approval:** required by class (`read_sensitive`, `write_file`, `delete_file`)
**Safety:** path normalization + root confinement + denylist checks.

---

## Command operations

### `POST /workspaces/{workspace_id}/commands/propose`
- Purpose: explain command plan/risk only

### `POST /workspaces/{workspace_id}/commands/run`
- Purpose: execute command
- **Status:** FUTURE, approval-gated, disabled by default

**Safety:** allowlist + risk scoring + explicit approval.

---

## Approvals

### `POST /approvals`
- Purpose: create approval request

### `GET /approvals`
- Purpose: list approvals

### `POST /approvals/{approval_id}/approve`
- Purpose: approve operation

### `POST /approvals/{approval_id}/reject`
- Purpose: reject operation

**Safety:** immutable audit trail, actor identity, operation payload hash.

---

## DEV-12A boundary

- This contract is draft-only.
- No route implementation is part of DEV-12A.
- `apply-patch` and `run-command` are future, approval-gated endpoints.
