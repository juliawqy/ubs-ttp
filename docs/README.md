# Documentation

Auto-generated from source code. Do not edit manually.

## Generate

```bash
make docs
# or
cd docs && bash generate.sh
```

## Contents

After running, `generated/` will contain:
- `shared/` — shared module class and function docs (pdoc)
- `recruitment/` — recruitment service docs
- `training/` — training service docs
- `performance/` — performance service docs
- `ai-assistant/` — AI assistant service docs
- `analytics/` — analytics service docs

## Tools used

- **pdoc** — auto-generates HTML from Python docstrings
- **FastAPI /docs** — each running service exposes OpenAPI docs at `/docs`
