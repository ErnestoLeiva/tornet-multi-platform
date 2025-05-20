# Docker Deployment Guide for Tornet

This guide will help you deploy the Tornet package using Docker and access the proxy from your local machine.

## Building and Running with Docker Compose

1. Build and start the container:

```bash
docker-compose up -d
```

This will build the Docker image and start the container in detached mode.

2. Check if the container is running:

```bash
docker-compose ps
```

## Using the Tornet Proxy

The Tor SOCKS proxy is now available at `127.0.0.1:4000`. You can configure your browser or applications to use this proxy:

### Firefox Configuration

1. Go to `Preferences` > `General` > `Network Settings`
2. Select `Manual proxy configuration`
3. Enter `127.0.0.1` for `SOCKS Host` and `4000` for the `Port`
4. Check the box `Proxy DNS when using SOCKS v5`
5. Click `OK`

### Other Applications

Configure your application to use a SOCKS5 proxy with:

- Host: 127.0.0.1
- Port: 4000

## Viewing Logs

To see the logs from the container:

```bash
docker-compose logs -f
```

## Stopping the Service

To stop the container:

```bash
docker-compose down
```

## Rebuilding After Changes

If you make changes to the code and need to rebuild:

```bash
docker-compose build
docker-compose up -d
```
