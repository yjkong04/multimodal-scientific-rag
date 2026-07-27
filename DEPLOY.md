# Deploying the API

The API runs the demo store, so it needs no database or API keys to go live.
Pick whichever host you have an account for. Both need the repo pushed to GitHub.

## Option A — Render (no local Docker required, recommended for day one)
1. Push this repo to GitHub (done — see the repo URL in the README badge).
2. Render dashboard → **New → Blueprint** → connect this repo.
3. Render reads [`render.yaml`](./render.yaml), builds the Dockerfile, and serves.
4. When it's live, hit `https://<your-service>.onrender.com/health`.

The free plan sleeps on idle, so the first request after a nap is slow — fine for a demo.

## Option B — Fly.io (needs flyctl + Docker locally)
```bash
brew install flyctl          # if not installed
fly auth login
fly launch --copy-config --no-deploy   # uses fly.toml, picks an app name
fly deploy
fly open                     # opens the live URL
```

## Verify a live deployment
```bash
BASE=https://<your-host>
curl -s $BASE/health
curl -s -X POST $BASE/ask -H 'content-type: application/json' \
  -d '{"question":"What does the figure show about dose and response?"}' | python3 -m json.tool
```

Once it's live, add the URL to the top of the README.
