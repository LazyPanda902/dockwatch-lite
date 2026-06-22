# dockwatch-lite

A lightweight homelab Docker container monitor. Query and watch running containers, check resource usage, and verify daemon connectivity with minimal dependencies.

## Installation

Install from source:

```bash
pip install -e .
```

Or install directly from the repository:

```bash
pip install git+https://github.com/yourusername/dockwatch-lite.git
```

## Usage

### List containers

List running containers only:

```bash
dockwatch list
```

List all containers including stopped ones:

```bash
dockwatch list --all
```

Alias:

```bash
dockwatch ls
```

### Watch containers

Continuously display container list with 3-second refresh (default):

```bash
dockwatch watch
```

Custom refresh interval (every 5 seconds):

```bash
dockwatch watch --interval 5
```

Watch all containers including stopped:

```bash
dockwatch watch --all
```

### View container stats

Get detailed resource usage for a running container:

```bash
dockwatch stats nginx
```

Shows:
- CPU percentage
- Memory usage and limit
- Network I/O (receive/transmit)
- Block I/O (read/write)

### Check daemon connectivity

Verify Docker daemon is reachable:

```bash
dockwatch ping
```

By default, `dockwatch` connects to `/var/run/docker.sock`. Specify a custom socket:

```bash
dockwatch --socket=/tmp/docker.sock list
```

## Global flags

- `--no-color` — disable ANSI colour output
- `--socket PATH` — path to Docker Unix socket (default: `/var/run/docker.sock`)

## Output formats

**List output** (running containers):

```
ID            NAME          IMAGE         STATE    UPTIME      PORTS
----------    -----         -----         -----    ------      -----
a1b2c3d4e5f6  nginx         nginx:latest  running  2h 15m      80->80/tcp
f6e5d4c3b2a1  db            postgres:14   running  1h 30m      5432->5432/tcp
```

**Stats output** (single container):

```
Container : nginx (a1b2c3d4e5f6)
State     : running
CPU       : 0.15%
Memory    : 24.5MB / 512.0MB  (4.8%)
Net I/O   : rx 125.3KB  tx 56.2KB
Block I/O : read 2.0MB  write 1.5MB
```

## Testing

Run the test suite with pytest:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=src tests/
```

Run specific test:

```bash
pytest tests/test_dockwatch.py::test_cmd_list_returns_zero_on_success
```

Tests cover:
- CLI argument parsing (commands, flags, aliases)
- Container info queries and uptime calculations
- Stats parsing (CPU, memory, network, block I/O)
- Table formatting and color output
- Error handling for missing/stopped containers
- Docker API communication
