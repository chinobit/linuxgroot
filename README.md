# My Zola Website - [linuxgroot.net](https://linuxgroot.net)

## Install with Docker
```
git clone https://github.com/chinobit/linuxgroot.git
cd linuxgroot
```
### Build
`docker run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app --rm ghcr.io/getzola/zola:v0.17.2 build`
### Serve
`docker run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app -p 8080:8080 -p 1024:1024 --rm ghcr.io/getzola/zola:v0.17.2 serve --interface 0.0.0.0 --port 8080 --base-url localhost`

> If you start from an empty local directory, you must init the app directory with a config.toml:
>
> `docker run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app -it --rm ghcr.io/getzola/zola:v0.17.2 init`
