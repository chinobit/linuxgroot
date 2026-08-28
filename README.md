# linuxgroot.net

Source for [linuxgroot.net](https://linuxgroot.net): a static site built with
[Zola](https://www.getzola.org) v0.22.1 and the [tabi](https://github.com/welpo/tabi)
theme, deployed to Cloudflare Workers Static Assets by GitHub Actions on push to `main`.

The theme is a git submodule pinned to a release tag, so clone with:

```
git clone --recurse-submodules <this repo>
```

## Local preview

```
podman run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app -p 8080:8080 --rm ghcr.io/getzola/zola:v0.22.1 serve --interface 0.0.0.0 --port 8080 --base-url localhost --drafts
```

Substitute `docker` for `podman` if that is what is installed. `--drafts` is local
only: CI builds without it, so `draft = true` pages never reach production.

## Build

```
podman run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app --rm ghcr.io/getzola/zola:v0.22.1 build
```

See `CLAUDE.md` for the project's architecture, privacy and security constraints.
