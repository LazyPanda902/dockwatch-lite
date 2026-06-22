# Usage Examples

## Basic Listing

List all running containers:

```bash
$ dockwatch list
ID            NAME          IMAGE         STATE    UPTIME      PORTS
----------    -----         -----         -----    ------      -----
a1b2c3d4e5f6  nginx         nginx:latest  running  2h 15m      80->80/tcp
f6e5d4c3b2a1  db            postgres:14   running  1h 30m      5432->5432/tcp
9876543210ab  app           app:v1.2.3    running  45m 30s      3000->3000/tcp
```

## Show All Containers

Include stopped containers:

```bash
$ dockwatch list --all
ID            NAME          IMAGE         STATE    UPTIME      PORTS
----------    -----         -----         -----    ------      -----
a1b2c3d4e5f6  nginx         nginx:latest  running  2h 15m      80->80/tcp
f6e5d4c3b2a1  db            postgres:14   running  1h 30m      5432->5432/tcp
abcdef123456  backup        backup:v2     exited   -           -
0987654321fe  test          test:dev      paused   -           -
```

## Watch Live Updates

Monitor containers continuously (refresh every 3 seconds, Ctrl-C to quit):

```bash
$ dockwatch watch
dockwatch-lite  (refresh every 3s — Ctrl-C to quit)

ID            NAME          IMAGE         STATE    UPTIME      PORTS
----------    -----         -----         -----    ------      -----
a1b2c3d4e5f6  nginx         nginx:latest  running  2h 15m      80->80/tcp
f6e5d4c3b2a1  db            postgres:14   running  1h 30m      5432->5432/tcp
```

(Screen refreshes every 3 seconds)

## Custom Refresh Interval

Watch with 10-second refresh:

```bash
$ dockwatch watch --interval 10
dockwatch-lite  (refresh every 10s — Ctrl-C to quit)
```

## View Container Stats

Check resource usage for a running container by name:

```bash
$ dockwatch stats nginx
Container : nginx (a1b2c3d4e5f6)
State     : running
CPU       : 0.32%
Memory    : 45.2MB / 512.0MB  (8.8%)
Net I/O   : rx 2.3MB  tx 1.1MB
Block I/O : read 12.5MB  write 8.3MB
```

By container ID (full or short):

```bash
$ dockwatch stats f6e5d4c3b2a1
Container : db (f6e5d4c3b2a1)
State     : running
CPU       : 2.15%
Memory    : 256.0MB / 2.0GB  (12.5%)
Net I/O   : rx 145.3MB  tx 89.2MB
Block I/O : read 450.2MB  write 230.5MB
```

## Check Daemon

Verify Docker daemon is reachable:

```bash
$ dockwatch ping
Docker daemon reachable at /var/run/docker.sock
```

Failed connection:

```bash
$ dockwatch ping
error: cannot reach Docker daemon at /var/run/docker.sock
```

## Custom Socket Path

Connect to a non-standard Docker socket:

```bash
$ dockwatch --socket=/tmp/docker.sock list
ID            NAME          IMAGE         STATE    UPTIME      PORTS
----------    -----         -----         -----    ------      -----
a1b2c3d4e5f6  nginx         nginx:latest  running  2h 15m      80->80/tcp
```

## Disable Color Output

For scripts or when piping output:

```bash
$ dockwatch --no-color list
ID            NAME          IMAGE         STATE    UPTIME      PORTS
a1b2c3d4e5f6  nginx         nginx:latest  running  2h 15m      80->80/tcp
```

## Error Cases

Container not found:

```bash
$ dockwatch stats missing_container
error: container 'missing_container' not found
```

Container not running:

```bash
$ dockwatch stats backup
error: container 'backup' is not running (state: exited)
```

No containers:

```bash
$ dockwatch list
No containers found.
```
