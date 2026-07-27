# Deploying the API

The API runs the demo store, so it needs no database or API keys to go live.
Everything below is Docker-based. The image builds and serves `/ask` as-is.

## Build and run locally
```bash
docker build -t paperlens:latest .
docker run --rm -p 8000:8000 paperlens:latest
curl -s localhost:8000/health
```

## Publish a public image to GHCR
A pullable image under your GitHub account — anyone can `docker run` it.
```bash
gh auth refresh -s write:packages           # one-time: grant package scope
gh auth token | docker login ghcr.io -u yjkong04 --password-stdin
docker build -t ghcr.io/yjkong04/paperlens:latest .
docker push ghcr.io/yjkong04/paperlens:latest
```
Then anyone can:
```bash
docker run -p 8000:8000 ghcr.io/yjkong04/paperlens:latest
```
The package starts private; make it public in the repo's Packages settings.

## Deploy a live URL on Fly.io (Docker-native)
`fly deploy` builds and pushes the Docker image and serves it over https.
```bash
fly auth login                              # one-time: browser login + card on file
fly launch --copy-config --no-deploy        # uses fly.toml, creates the app
fly deploy                                   # builds Docker image, ships it
fly open                                      # opens the live URL
```

## Verify a live deployment
```bash
BASE=https://<your-host>
curl -s $BASE/health
curl -s -X POST $BASE/ask -H 'content-type: application/json' \
  -d '{"question":"What does the figure show about dose and response?"}' | python3 -m json.tool
```

Once it's live, add the URL to the top of the README.
