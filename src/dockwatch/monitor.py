"""Docker socket client and container monitoring primitives."""

from __future__ import annotations

import http.client
import json
import socket
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class _UnixHTTPConnection(http.client.HTTPConnection):
    """HTTP connection that speaks over a Unix domain socket."""

    def __init__(self, socket_path: str) -> None:
        super().__init__("localhost")
        self._socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self._socket_path)
        self.sock = sock


@dataclass(frozen=True)
class ContainerInfo:
    id: str
    name: str
    image: str
    status: str
    state: str
    created: int
    ports: list[str] = field(default_factory=list)

    @property
    def short_id(self) -> str:
        return self.id[:12]

    @property
    def uptime_seconds(self) -> int:
        now = int(datetime.now(timezone.utc).timestamp())
        return max(0, now - self.created)

    @property
    def uptime_human(self) -> str:
        secs = self.uptime_seconds
        if secs < 60:
            return f"{secs}s"
        if secs < 3600:
            return f"{secs // 60}m {secs % 60}s"
        hours = secs // 3600
        mins = (secs % 3600) // 60
        return f"{hours}h {mins}m"

    @property
    def is_running(self) -> bool:
        return self.state.lower() == "running"


@dataclass(frozen=True)
class ContainerStats:
    container_id: str
    cpu_percent: float
    mem_usage_bytes: int
    mem_limit_bytes: int
    net_rx_bytes: int
    net_tx_bytes: int
    block_read_bytes: int
    block_write_bytes: int

    @property
    def mem_percent(self) -> float:
        if self.mem_limit_bytes == 0:
            return 0.0
        return round(self.mem_usage_bytes / self.mem_limit_bytes * 100, 2)

    @staticmethod
    def _human(value: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024:
                return f"{value:.1f}{unit}"
            value //= 1024
        return f"{value:.1f}TB"

    @property
    def mem_usage_human(self) -> str:
        return self._human(self.mem_usage_bytes)

    @property
    def mem_limit_human(self) -> str:
        return self._human(self.mem_limit_bytes)

    @property
    def net_rx_human(self) -> str:
        return self._human(self.net_rx_bytes)

    @property
    def net_tx_human(self) -> str:
        return self._human(self.net_tx_bytes)


def _parse_cpu_percent(raw: dict[str, Any]) -> float:
    cpu = raw.get("cpu_stats", {})
    precpu = raw.get("precpu_stats", {})

    cpu_delta = cpu.get("cpu_usage", {}).get("total_usage", 0) - precpu.get(
        "cpu_usage", {}
    ).get("total_usage", 0)
    system_delta = cpu.get("system_cpu_usage", 0) - precpu.get("system_cpu_usage", 0)
    num_cpus = len(cpu.get("cpu_usage", {}).get("percpu_usage") or []) or 1

    if system_delta <= 0 or cpu_delta < 0:
        return 0.0
    return round((cpu_delta / system_delta) * num_cpus * 100.0, 2)


def _parse_net_io(raw: dict[str, Any]) -> tuple[int, int]:
    networks = raw.get("networks", {})
    rx = sum(v.get("rx_bytes", 0) for v in networks.values())
    tx = sum(v.get("tx_bytes", 0) for v in networks.values())
    return rx, tx


def _parse_block_io(raw: dict[str, Any]) -> tuple[int, int]:
    entries = raw.get("blkio_stats", {}).get("io_service_bytes_recursive") or []
    read_b = sum(e.get("value", 0) for e in entries if e.get("op") == "Read")
    write_b = sum(e.get("value", 0) for e in entries if e.get("op") == "Write")
    return read_b, write_b


class DockerClient:
    """Minimal Docker API client that communicates over the Unix socket."""

    def __init__(self, socket_path: str = "/var/run/docker.sock") -> None:
        self._socket_path = socket_path

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = path
        if params:
            url = f"{path}?{urllib.parse.urlencode(params)}"
        conn = _UnixHTTPConnection(self._socket_path)
        try:
            conn.request("GET", url, headers={"Host": "localhost"})
            response = conn.getresponse()
            body = response.read().decode("utf-8")
            if response.status not in (200, 201, 204):
                raise RuntimeError(
                    f"Docker API {response.status} for {url}: {body[:200]}"
                )
            return json.loads(body) if body else {}
        finally:
            conn.close()

    def ping(self) -> bool:
        try:
            self._get("/_ping")
            return True
        except Exception:
            return False

    def list_containers(self, all_containers: bool = False) -> list[ContainerInfo]:
        params = {"all": "true"} if all_containers else {}
        raw_list: list[dict[str, Any]] = self._get("/containers/json", params)

        results: list[ContainerInfo] = []
        for c in raw_list:
            name = (c.get("Names") or ["unknown"])[0].lstrip("/")
            ports: list[str] = []
            for p in c.get("Ports") or []:
                if p.get("PublicPort"):
                    ports.append(f"{p['PublicPort']}->{p['PrivatePort']}/{p['Type']}")

            results.append(
                ContainerInfo(
                    id=c.get("Id", ""),
                    name=name,
                    image=c.get("Image", "unknown"),
                    status=c.get("Status", "unknown"),
                    state=c.get("State", "unknown"),
                    created=c.get("Created", 0),
                    ports=ports,
                )
            )
        return results

    def get_stats(self, container_id: str) -> ContainerStats:
        raw: dict[str, Any] = self._get(
            f"/containers/{container_id}/stats", {"stream": "false"}
        )
        mem = raw.get("memory_stats", {})
        mem_usage = mem.get("usage", 0)
        mem_limit = mem.get("limit", 0)
        rx, tx = _parse_net_io(raw)
        blk_r, blk_w = _parse_block_io(raw)
        return ContainerStats(
            container_id=container_id,
            cpu_percent=_parse_cpu_percent(raw),
            mem_usage_bytes=mem_usage,
            mem_limit_bytes=mem_limit,
            net_rx_bytes=rx,
            net_tx_bytes=tx,
            block_read_bytes=blk_r,
            block_write_bytes=blk_w,
        )

    def get_container(self, name_or_id: str) -> ContainerInfo | None:
        for c in self.list_containers(all_containers=True):
            if c.name == name_or_id or c.short_id == name_or_id or c.id == name_or_id:
                return c
        return None
