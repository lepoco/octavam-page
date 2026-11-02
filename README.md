# Octavam

[octavam.com](https://octavam.com) — website for the free piano learning app.
[App source](https://github.com/lepoco/octavam).

Polish by default. English, German, French, Ukrainian and Russian follow browser preferences. Manual language choices are remembered.

## Preview

Python 3.9+:

```sh
python3 scripts/build-site.py
python3 -m http.server 8080 --directory .build/site
```

## Deployment

Select **GitHub Actions** in GitHub Pages settings. Pushes to `main` deploy to `octavam.com`.

Set the numeric `app_store_id` in `site-config.json` to enable app links and the Safari banner. With `null`, buttons link to the App Store homepage.
