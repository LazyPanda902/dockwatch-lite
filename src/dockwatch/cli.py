"""CLI entry point for dockwatch-lite."""

from __future__ import annotations

import argparse
import sys
import time

from dockwatch.monitor import ContainerInfo, ContainerStats, DockerClient

_COL_STATE = {"running": "\033[32m", "exited": "\033[31m", "paused": "\033[33m"}
_RESET = "\033[0m"


def _state_color(state: str) -> str:
    return _COL_STATE.get(state.lower(), "")


def _fmt_state(state: str, use_color: bool) -> str:
    if not use_color:
        return state
    return f"{_state_color(state)}{state}{_RESET}"


def _table_row(*cells: str, widths: list[int]) -> str:
    return "  ".join(str(c).ljust(w) for c, w in zip(cells, widths))


def _print_container_table(
    containers: list[ContainerInfo], use_color: bool, show_all: bool
) -> None:
    if not show_all:
        containers = [c for c in containers if c.is_running]

    if not containers:
        print("No containers found.")
        return

    headers = ["ID", "NAME", "IMAGE", "STATE", "UPTIME", "PORTS"]
    rows = [
        (
            c.short_id,
            c.name[:30],
            c.image[:30],
            _fmt_state(c.state, use_color),
            c.uptime_human if c.is_running else "-",
            ", ".join(c.ports) if c.ports else "-",
        )
        for c in containers
    ]

    plain_rows = [
        (c.short_id, c.name[:30], c.image[:30], c.state, "", ", ".join(c.ports) or "-")
        for c in containers
    ]

    widths = [
        max(len(h), max((len(str(r[i])) for r in plain_rows), default=0))
        for i, h in enumerate(headers)
    ]

    sep = "  ".join("-" * w for w in widths)
    print(_table_row(*headers, widths=widths))
    print(sep)
    for row in rows:
        print(_table_row(*row, widths=widths))


def _print_stats(stats: ContainerStats, info: ContainerInfo, use_color: bool) -> None:
    print(f"Container : {info.name} ({info.short_id})")
    print(f"State     : {_fmt_state(info.state, use_color)}")
    print(f"CPU       : {stats.cpu_percent:.2f}%")
    print(
        f"Memory    : {stats.mem_usage_human} / {stats.mem_limit_human}"
        f"  ({stats.mem_percent:.1f}%)"
    )
    print(f"Net I/O   : rx {stats.net_rx_human}  tx {stats.net_tx_human}")
    print(
        f"Block I/O : read {ContainerStats._human(stats.block_read_bytes)}"
        f"  write {ContainerStats._human(stats.block_write_bytes)}"
    )


def cmd_list(args: argparse.Namespace, client: DockerClient) -> int:
    try:
        containers = client.list_containers(all_containers=args.all)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_container_table(containers, use_color=not args.no_color, show_all=args.all)
    return 0


def cmd_stats(args: argparse.Namespace, client: DockerClient) -> int:
    info = client.get_container(args.container)
    if info is None:
        print(f"error: container '{args.container}' not found", file=sys.stderr)
        return 1
    if not info.is_running:
        print(f"error: container '{info.name}' is not running (state: {info.state})", file=sys.stderr)
        return 1
    try:
        stats = client.get_stats(info.id)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_stats(stats, info, use_color=not args.no_color)
    return 0


def cmd_watch(args: argparse.Namespace, client: DockerClient) -> int:
    interval = max(1, args.interval)
    try:
        while True:
            print("\033[2J\033[H", end="")  # clear screen
            print(f"dockwatch-lite  (refresh every {interval}s — Ctrl-C to quit)\n")
            containers = client.list_containers(all_containers=args.all)
            _print_container_table(
                containers, use_color=not args.no_color, show_all=args.all
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_ping(args: argparse.Namespace, client: DockerClient) -> int:
    ok = client.ping()
    if ok:
        print(f"Docker daemon reachable at {args.socket}")
    else:
        print(f"error: cannot reach Docker daemon at {args.socket}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="dockwatch",
        description="Lightweight homelab Docker container monitor",
    )
    root.add_argument(
        "--socket",
        default="/var/run/docker.sock",
        metavar="PATH",
        help="path to the Docker Unix socket (default: /var/run/docker.sock)",
    )
    root.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI colour output",
    )

    sub = root.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # list
    p_list = sub.add_parser("list", aliases=["ls"], help="list containers")
    p_list.add_argument(
        "-a", "--all",
        action="store_true",
        help="include stopped containers",
    )

    # stats
    p_stats = sub.add_parser("stats", help="show resource stats for one container")
    p_stats.add_argument("container", metavar="NAME_OR_ID")

    # watch
    p_watch = sub.add_parser("watch", help="continuously refresh container list")
    p_watch.add_argument(
        "-n", "--interval",
        type=int,
        default=3,
        metavar="SECONDS",
        help="refresh interval in seconds (default: 3)",
    )
    p_watch.add_argument(
        "-a", "--all",
        action="store_true",
        help="include stopped containers",
    )

    # ping
    sub.add_parser("ping", help="check connectivity to the Docker daemon")

    return root


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    client = DockerClient(socket_path=args.socket)

    dispatch = {
        "list": cmd_list,
        "ls": cmd_list,
        "stats": cmd_stats,
        "watch": cmd_watch,
        "ping": cmd_ping,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args, client)


if __name__ == "__main__":
    sys.exit(main())
