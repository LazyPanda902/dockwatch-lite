# Configuration

dockwatch-lite has minimal configuration. All behavior is controlled via command-line arguments.

## Socket Path

By default, dockwatch connects to the standard Docker socket at `/var/run/docker.sock`.

To use a custom socket, pass `--socket`:

```bash
dockwatch --socket=/var/run/docker-custom.sock list
```

This is useful when:
- Running Docker via rootless mode
- Using Docker contexts with custom socket paths
- Accessing Docker from inside a container with a volume mount
- Testing against mock Docker endpoints

## Environment Setup

No environment variables are required or used by dockwatch-lite.

### Socket Permissions

Ensure the user running dockwatch has read access to the Docker socket:

```bash
# Check socket permissions
ls -la /var/run/docker.sock

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Verify connectivity
dockwatch ping
```

### Running in Containers

If running dockwatch inside a Docker container, mount the socket:

```bash
docker run -it -v /var/run/docker.sock:/var/run/docker.sock dockwatch-lite dockwatch list
```

## Command-Line Reference

All configuration is via flags:

- `--socket PATH` — Docker socket path (default: `/var/run/docker.sock`)
- `--no-color` — disable ANSI colors in output
- `-n, --interval SECONDS` — refresh interval for `watch` command (default: 3)
- `-a, --all` — show all containers including stopped (for `list` and `watch`)

Examples:

```bash
# Watch all containers every 5 seconds without color
dockwatch --no-color watch --all --interval 5

# List all containers from custom socket
dockwatch --socket=/custom/docker.sock list --all

# Get stats for container with no color output
dockwatch --no-color stats mycontainer
```
