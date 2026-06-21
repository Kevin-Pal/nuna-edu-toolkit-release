# Nuna-Edu-Toolkit

**A self-hostable toolkit for collecting and annotating first-person ambient audio — and turning it into research datasets.**

Nuna-Edu-Toolkit is an open toolkit from the AIoT Lab at The Chinese University of Hong Kong. Audio captured by the *Nuna* wearable (a smart necklace) is streamed
to a server you control, sliced into 1-minute segments, optionally pre-labeled with ASR,
and annotated through a web app using a flexible, event-driven schema. Participants stay in
control: they choose which recordings to share and can delete the rest.

- 🌐 **Project site & demo:** https://kevin-pal.github.io/nuna-edu-toolkit-release/
- 🕹️ **Live demo (no install):** https://kevin-pal.github.io/nuna-edu-toolkit-release/demo/
- 📱 **Data-collection app (Android, internal beta):** https://www.pgyer.com/nuna-android-cas
- 📖 **Documentation (English / 中文):** https://kevin-pal.github.io/nuna-edu-toolkit-release/docs/

> The hosted demo runs entirely in your browser with sample data — nothing is saved.
> Self-host this repo for the full experience.

---

## Features

- **First-person audio capture** via the Nuna wearable → your own ingest server.
- **1-minute segmentation** with time-grouped browsing (hour → quarter → minute).
- **ASR-assisted recall:** per-segment speech-to-text previews via a pluggable provider — bring your own ASR model (Alibaba DashScope Qwen3-ASR included); a no-credentials placeholder is bundled for offline runs.
- **Event-driven, multi-granularity annotation:** *Block* labels for continuous events (scene / behavior / emotion) and *Point* labels for finer sub-events.
- **Swappable label schema** — the web-based forms are easy to repurpose for other dataset tasks.
- **Privacy-first:** participants pick what to share and can delete recordings.
- **Self-hostable** with Docker Compose; SQLite by default, config fully externalized (12-factor).
- **Bilingual UI** (English / 简体中文).

## Documentation

A bilingual (English / 简体中文) guide is published on the project site:
**[Documentation »](https://kevin-pal.github.io/nuna-edu-toolkit-release/docs/)**

It covers the workflow this toolkit is built around — a **self-recall annotation** method for
building **first-person (ego) audio datasets** — including how participants collect and annotate
data, how to self-host the platform, the block + point label schema, and the research tasks the
resulting dataset supports (ASC, SED, VAD, HAR, affective computing, first-person perception, and
more) plus open research directions.

## Architecture

| Service | Path | Purpose |
|---|---|---|
| `app` | `app/` | FastAPI + Jinja2 web app (browse, ASR preview, annotate). SQLite via SQLAlchemy. |
| `receiver` | `app/backend/receiver_main.py` | Audio ingest endpoint (the wearable's phone app uploads here). |
| `prelabel-service` | `prelabel_service/` | Pre-labeling (ASR) pipeline. |
| `runtime` | `runtime/` | Data, env, logs — **not** tracked by git; mounted into containers. |

Frontend is server-rendered HTML (Jinja2) + Bootstrap 5 + vanilla JS — no Node build step.

## Quickstart (self-host)

Requires Docker + Docker Compose.

```bash
git clone https://github.com/Kevin-Pal/nuna-edu-toolkit-release.git
cd nuna-edu-toolkit-release

# 1) Create runtime dirs + default env files
./scripts/init-runtime.sh

# 2) Review/edit configuration (see runtime/env/*.env.example for all options)
#    At minimum, set a strong SESSION_SECRET in runtime/env/app.env
#    and point CUSTOMER_SERVER_URL at your audio source.

# 3) Build & start the stack (app + receiver + prelabel-service)
./scripts/deploy.sh -d
```

The web app is then served on the host `APP_PORT` (default `8080`, see `compose/.env`).
Open it, register with your Nuna user ID, and start annotating.

## Configuration

Environment is split across `runtime/env/*.env` (in-container) and `compose/.env` (host ports).
Copy the provided `*.env.example` files (or run `init-runtime.sh`). Key variables:

| Variable | Where | Notes |
|---|---|---|
| `SESSION_SECRET` | `runtime/env/app.env` | **Change in production.** Long random string. |
| `CUSTOMER_SERVER_URL` | `runtime/env/app.env` | Your audio source / receiver URL. |
| `DASHSCOPE_API_KEY` | host env / `compose/.env` | Only if using DashScope ASR. Never commit it. |
| `PRELABEL_ASR_PROVIDER` | `runtime/env/prelabel.env` | `mock` (default) or `dashscope_qwen3_asr_flash`. |
| `APP_PORT` / `DATA_PORT` / `PRELABEL_PORT` | `compose/.env` | Host port mappings. |

> Secrets live only in `runtime/` (git-ignored). Only `*.env.example` templates are committed.

## Repository layout

```
app/                 Web app (backend FastAPI + Jinja2 frontend) & receiver
prelabel_service/    ASR pre-label microservice
compose/             Docker Compose files + .env.example
runtime/             Runtime data/env/logs (git-ignored; structure via .gitkeep)
scripts/             init-runtime / deploy / snapshot helpers
snippets/            Reference code snippets (ASR call, DB inspector, receiver)
docs/                Design notes (original spec; Chinese)
site/                Promotional GitHub Pages site + static browser demo + bilingual docs
tools/               Reproducible generators (QR codes, promo poster/OG image, one-page PPT)
promo/               Generated promo assets (one-page slide, social copy, poster)
.github/             GitHub Actions workflow that deploys site/ to Pages
```

## Promotion site & demo

The `site/` directory is a static GitHub Pages site (landing page + no-backend browser
demo) for showcasing the toolkit. It is deployed by `.github/workflows/pages.yml`.
QR codes are regenerated reproducibly with `python tools/generate_qr.py`.

## The Nuna pendant

First-person audio is captured by **Nuna**, ThingX's AI emotion-tracking pendant.
Get one from [thingx.ai](https://www.thingx.ai/products/nuna-emotion-tracking-pendants) ·
[Amazon](https://www.amazon.com/NUNA-Pendant-Monitoring-Mindfulness-Meditation/dp/B0G4QJG5QR) ·
[JD.com (京东)](https://3.cn/2SU-kIe1?jkl=@IEWKw4KAc2@).

## Credits

Nuna-Edu-Toolkit — Anlan Peng, Ruihan Xie, Yihang Su, Siyang Jiang, Zhiyuan Xie, Zhenyu Yan, Guoliang Xing.
[AIoT Lab](https://aiot.ie.cuhk.edu.hk/), The Chinese University of Hong Kong.

**Contact:** Anlan Peng — [pa025@ie.cuhk.edu.hk](mailto:pa025@ie.cuhk.edu.hk) · [AIoT Lab, CUHK](https://aiot.ie.cuhk.edu.hk/)

## Citation

If you use Nuna-Edu-Toolkit, a dataset collected with it, or a research direction from our
[documentation](https://kevin-pal.github.io/nuna-edu-toolkit-release/docs/) in academic or other
work, **please cite this work.** GitHub's "Cite this repository" button (backed by
[`CITATION.cff`](CITATION.cff)) produces the reference below:

```bibtex
@software{Peng_Nuna_Edu_Toolkit_2026,
  author = {Peng, Anlan and Xie, Ruihan and Su, Yihang and Jiang, Siyang and
            Xie, Zhiyuan and Yan, Zhenyu and Xing, Guoliang},
  title  = {{Nuna-Edu-Toolkit: A Self-Hostable Platform for Collecting and
            Annotating First-Person Audio Datasets}},
  year   = {2026},
  url    = {https://github.com/Kevin-Pal/nuna-edu-toolkit-release},
  note   = {AIoT Lab, The Chinese University of Hong Kong.
            Source-available under PolyForm Noncommercial 1.0.0}
}
```

The code, the documentation, and datasets produced with the toolkit are © 2026 the authors;
commercial use requires a separate license (see below).

## License

Licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)** (SPDX: `PolyForm-Noncommercial-1.0.0`).

You may use, modify, and share this software for **noncommercial** purposes — research,
teaching, and personal use. **Commercial use requires a separate license; please contact the
authors.** Because it restricts commercial use, this is a *source-available* license, not an
OSI-approved "open source" license.
