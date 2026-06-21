# Release Scrub Manifest — Nuna-Edu-Toolkit

This document records every item removed, anonymized, or flagged when producing the public
release from the private source repo (`ref/CodeRepo-nuna-audio-lab-app`, 18 commits).

**Release strategy:** the public repo (this tree) is a **fresh single squash commit** with no
inherited history. The private source and its git history are **not published** (kept under
`/ref/`, which is git-ignored). Therefore secrets that only ever lived in source *history*
cannot leak via this release — **but live credentials must still be rotated** (see §4).

---

## 1. Removed entirely (excluded from the release)

| Item | Reason | Severity |
|---|---|---|
| `snippets/s3_audio_downloader.py` | **Hardcoded live AWS access key + secret** (`AKIA…`), S3 bucket `<redacted-bucket>` (us-east-1). Also contained a **userId → real-name mapping** (PII, e.g. `<participant-id>` → a real person). | **CRITICAL** |
| `AGENTS.md` | Internal AI-agent development spec (~20 KB); dev metadata not meant for public. | MEDIUM |
| `.vscode/` | Editor settings; dev metadata. | LOW |
| `docs/to-do-list.md` | Internal TODO notes (incl. a plan to store AWS keys); dev metadata. | MEDIUM |
| `docs/` (all design notes) | Original internal design specs, Chinese-only and dev-process flavored; superseded by the public bilingual docs at `site/docs/`. Removed from the public release. (No secrets — see §3.) | LOW |
| `compose/.env`, `runtime/env/app.env`, `runtime/env/stack.env`, `runtime/env/prelabel.env` | Tracked environment files. Replaced with `*.env.example` templates; `.gitignore` updated so real env files are never tracked again. (Values were non-secret placeholders — see §3.) | MEDIUM |
| `.git/` (source history) | Not carried into the release; the release is a clean single commit. | — |
| `runtime/env/gateway.env` | Already deleted upstream; existed only in source history; absent from release. | LOW |

## 2. Scrubbed in place (edited, file retained)

| File:line | Before | After |
|---|---|---|
| `app/backend/routers/auth.py:76` | default `http://120.79.x.x (redacted):9000/` (real server IP) | `http://localhost:9000/` |
| `app/backend/routers/tasks.py:122` | default `http://120.79.x.x (redacted):9000/` | `http://localhost:9000/` |
| `snippets/qwen3-asr-flash_DashScope_LocalFile.py:9` | `/home/<dev-user>/nuna-audio-lab-app/...<participant-id>/20260318/...wav` (dev username + real userId) | `/path/to/nuna-edu-toolkit/runtime/data/audio/<user_id>/<date>/<segment>.wav` |
| `snippets/db_read.py:8` | `# filepath: /home/<dev-user>/nuna-audio-lab-app/...` (dev username) | `# filepath: /path/to/nuna-edu-toolkit/snippets/db_read.py` |

## 3. Verified clean (checked; no action needed)

- **No real audio or database** committed — `runtime/data/` contains only `.gitkeep`.
- **`DASHSCOPE_API_KEY`** never held a value in the working tree or in any history commit (no rotation needed).
- **`SESSION_SECRET`** only ever the placeholder `dev_secret_please_change`.
- `prelabel_service/` reads the API key from environment only (no hardcoded secret).
- `compose/*.yml`, Dockerfiles, and the other `scripts/*.sh` contain no secrets or PII.
- Post-scrub scan of the release tree for `120.79`, `<dev-user>`, `<participant-id>`, `AKIA`, AWS secret → **0 matches** (all remaining hits are confined to the git-ignored `/ref/`).

## 4. Keys to ROTATE (action required by the owner)

- **AWS access key `AKIA…(redacted)`** (and its secret) — was committed *live* into the
  source repo's history (`snippets/s3_audio_downloader.py`, all 18 commits). Even though the
  source history is not published, the key has resided in a git repo and is active. **Deactivate
  / delete / rotate it in AWS IAM.** Audit S3 bucket `<redacted-bucket>` access if warranted.

## 5. Retained intentionally (not sensitive)

- **pgyer download link** `https://www.pgyer.com/nuna-android-cas` — public; this is the app we are promoting.
- **`/thingx/api/file/upload/audio`** endpoint — part of the wearable→server upload contract, not a secret.
