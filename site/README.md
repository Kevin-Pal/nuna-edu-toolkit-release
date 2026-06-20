# Promotional site (`site/`)

Static GitHub Pages site for Nuna-Edu-Toolkit: a landing/hub page plus a
no-backend browser demo. Pure static files — no server, no database, nothing saved.

```
site/
├── index.html              Landing / hub page (hero, how-it-works, features, 3 cards)
├── assets/
│   ├── css/landing.css     Landing styles
│   └── qr/                 Generated QR codes (PNG + SVG): app, repo, site
└── demo/                   Static, no-backend product demo
    ├── index.html          Sign-in (cosmetic) → tasks
    ├── tasks.html          Day list (annotation tasks)
    ├── task.html           Label desk — segment selection + Create Block  ← the hero screen
    ├── block.html          Block detail + Point annotation
    ├── prelabel.html       ASR pre-label console (simulated run)
    └── assets/
        ├── css/style.css   Mirrored from app/frontend/static/css (the real app styles)
        ├── css/demo.css    Demo-only banner / toast
        ├── js/app.js, task_detail.js, block_detail.js   Mirrored real frontend JS
        ├── js/demo.js      Sample audio + time rendering + stubbed (non-saving) mutations
        └── audio.js        Generated tiny sample tone (data URI) — no real recordings
```

## Deploy (GitHub Pages via Actions)

1. Push this repo to `github.com/Kevin-Pal/nuna-edu-toolkit-release`.
2. In the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The workflow `.github/workflows/pages.yml` publishes `site/` on every push to `main`
   (or run it manually from the Actions tab).
4. Live at **https://kevin-pal.github.io/nuna-edu-toolkit-release/** ; demo at `…/demo/`.

All asset links are **relative**, so the site works correctly under the
`/nuna-edu-toolkit-release/` project sub-path.

## Reproduce the generated assets

```bash
pip install segno
python tools/generate_qr.py        # → site/assets/qr/{app,repo,site}.{png,svg}
python tools/gen_sample_audio.py   # → site/demo/assets/audio.js
```

To repoint a QR (e.g. host the APK on a GitHub Release), edit the URL in
`tools/generate_qr.py` and re-run it.

## Keep the demo faithful to the app

`site/demo/assets/{css/style.css,js/app.js,js/task_detail.js,js/block_detail.js}` are
copies of `app/frontend/static/...`. If the real frontend changes, re-copy them:

```bash
cp app/frontend/static/css/style.css       site/demo/assets/css/style.css
cp app/frontend/static/js/app.js           site/demo/assets/js/app.js
cp app/frontend/static/js/task_detail.js   site/demo/assets/js/task_detail.js
cp app/frontend/static/js/block_detail.js  site/demo/assets/js/block_detail.js
```
