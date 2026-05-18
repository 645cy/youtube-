# TubeFactory OCP

<!-- CRG: Root README is the stable entry point for setup, integration, and daily usage. -->

TubeFactory OCP is a YouTube research and content-operations workspace. It combines a FastAPI backend, a Next.js dashboard, YouTube data ingestion, analysis endpoints, and content-factory workflows.

## Quick Start

1. Create or update `.env` in the project root.

```env
YOUTUBE_API_KEY=your_youtube_data_api_key
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_PREFIX=/api/v1
```

2. Start the local stack.

```powershell
.\start-dev.ps1
```

3. Open the web app.

```text
http://127.0.0.1:3000
```

4. Check integration health first.

```text
http://127.0.0.1:3000/settings/integrations
```

## Daily Workflow

Use the site in this order:

1. `Settings > Integrations`: confirm the YouTube key is configured and diagnostics pass.
2. `Workspace`: use the guided entry for common jobs.
3. `Channels`: add or discover competitor channels.
4. `Videos`: import known videos or review videos discovered from channels.
5. `Analysis`: run viral, evergreen, sentiment, monetization, format, and growth checks.
6. `Factory`: turn discovered topics into titles, scripts, shot lists, SEO keywords, and publishing plans.
7. `Radar`: monitor recurring jobs and growth signals.

## Data Trust Rules

The app should not pretend failed fetches are empty data.

- Sentiment analysis returns `status=skipped` when no real comments are available.
- Growth rows include `source=metric_history` or `source=estimated`.
- YouTube comments require working API access; yt-dlp fallback does not provide comments.
- The integration diagnostics page is the first place to check when YouTube data looks empty.

## Verification

Run these before treating a change as stable:

```powershell
python -m pytest tests -q
npm.cmd run type-check --prefix apps\web
python -m flake8 apps\api\routers\analysis.py apps\api\routers\crawler.py apps\api\routers\videos.py --select=E501,F821,F401 --jobs=1 --count
```

## Architecture

- `apps/api`: FastAPI backend and router layer.
- `apps/web`: Next.js frontend.
- `packages/db`: shared SQLAlchemy schema and session setup.
- `tests`: backend regression tests.
- `data`: local SQLite data and backups.

The current development priority is stability before feature expansion: keep request schemas explicit, avoid fake fallback data, keep generated build artifacts out of Git, and add regression tests for every fixed production bug.
