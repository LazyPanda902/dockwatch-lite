"""Tests for dockwatch-lite CLI and core monitoring logic."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from dockwatch.cli import (
    _fmt_state,
    _state_color,
    _table_row,
    build_parser,
    cmd_list,
    cmd_ping,
    cmd_stats,
)
from dockwatch.monitor import (
    ContainerInfo,
    ContainerStats,
    _parse_block_io,
    _parse_cpu_percent,
    _parse_net_io,
)


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    assert parser.prog == "dockwatch"


def test_build_parser_list_subcommand():
    parser = build_parser()
    args = parser.parse_args(["list"])
    assert args.command == "list"
    assert args.all is False
    assert args.no_color is False


def test_build_parser_list_alias_ls():
    parser = build_parser()
    args = parser.parse_args(["ls"])
    assert args.command == "ls"


def test_build_parser_list_all_flag():
    parser = build_parser()
    args = parser.parse_args(["list", "--all"])
    assert args.all is True


def test_build_parser_stats_subcommand():
    parser = build_parser()
    args = parser.parse_args(["stats", "mycontainer"])
    assert args.command == "stats"
    assert args.container == "mycontainer"


def test_build_parser_watch_defaults():
    parser = build_parser()
    args = parser.parse_args(["watch"])
    assert args.command == "watch"
    assert args.interval == 3
    assert args.all is False


def test_build_parser_watch_interval():
    parser = build_parser()
    args = parser.parse_args(["watch", "--interval=10"])
    assert args.interval == 10


def test_build_parser_watch_short_interval():
    parser = build_parser()
    args = parser.parse_args(["watch", "-n", "5"])
    assert args.interval == 5


def test_build_parser_ping_subcommand():
    parser = build_parser()
    args = parser.parse_args(["ping"])
    assert args.command == "ping"


def test_build_parser_custom_socket():
    parser = build_parser()
    args = parser.parse_args(["--socket=/tmp/docker.sock", "ping"])
    assert args.socket == "/tmp/docker.sock"


def test_build_parser_no_color_flag():
    parser = build_parser()
    args = parser.parse_args(["--no-color", "list"])
    assert args.no_color is True


def test_build_parser_missing_subcommand_exits():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([])
    assert exc_info.value.code == 2


def test_build_parser_unknown_subcommand_exits():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["bogus"])
    assert exc_info.value.code == 2


def test_build_parser_stats_missing_positional_exits():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["stats"])
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# ContainerInfo
# ---------------------------------------------------------------------------

def _make_container(**overrides) -> ContainerInfo:
    defaults = dict(
        id="abcdef123456789012",
        name="web",
        image="nginx:latest",
        status="Up 2 hours",
        state="running",
        created=0,
        ports=["80->80/tcp"],
    )
    defaults.update(overrides)
    return ContainerInfo(**defaults)


def test_container_info_short_id():
    c = _make_container(id="abcdef123456789012")
    assert c.short_id == "abcdef123456"


def test_container_info_is_running_true():
    c = _make_container(state="running")
    assert c.is_running is True


def test_container_info_is_running_false():
    c = _make_container(state="exited")
    assert c.is_running is False


def test_container_info_is_running_case_insensitive():
    c = _make_container(state="Running")
    assert c.is_running is True


def test_container_info_uptime_seconds_non_negative():
    import time
    created = int(time.time()) - 120
    c = _make_container(created=created)
    assert c.uptime_seconds >= 119


def test_container_info_uptime_human_seconds():
    import time
    created = int(time.time()) - 45
    c = _make_container(created=created)
    assert c.uptime_human.endswith("s")


def test_container_info_uptime_human_minutes():
    import time
    created = int(time.time()) - 150
    c = _make_container(created=created)
    assert "m" in c.uptime_human


def test_container_info_uptime_human_hours():
    import time
    created = int(time.time()) - 7500
    c = _make_container(created=created)
    assert "h" in c.uptime_human


def test_container_info_no_ports():
    c = _make_container(ports=[])
    assert c.ports == []


# ---------------------------------------------------------------------------
# ContainerStats
# ---------------------------------------------------------------------------

def _make_stats(**overrides) -> ContainerStats:
    defaults = dict(
        container_id="abc123",
        cpu_percent=12.5,
        mem_usage_bytes=512 * 1024 * 1024,
        mem_limit_bytes=2 * 1024 * 1024 * 1024,
        net_rx_bytes=1024,
        net_tx_bytes=2048,
        block_read_bytes=4096,
        block_write_bytes=8192,
    )
    defaults.update(overrides)
    return ContainerStats(**defaults)


def test_stats_mem_percent():
    s = _make_stats(mem_usage_bytes=512, mem_limit_bytes=1024)
    assert s.mem_percent == 50.0


def test_stats_mem_percent_zero_limit():
    s = _make_stats(mem_usage_bytes=512, mem_limit_bytes=0)
    assert s.mem_percent == 0.0


def test_stats_human_bytes():
    assert ContainerStats._human(512) == "512.0B"


def test_stats_human_kilobytes():
    assert ContainerStats._human(2048) == "2.0KB"


def test_stats_human_megabytes():
    assert ContainerStats._human(3 * 1024 * 1024) == "3.0MB"


def test_stats_human_gigabytes():
    assert ContainerStats._human(2 * 1024 * 1024 * 1024) == "2.0GB"


def test_stats_mem_usage_human():
    s = _make_stats(mem_usage_bytes=1024)
    assert s.mem_usage_human == "1.0KB"


def test_stats_net_rx_human():
    s = _make_stats(net_rx_bytes=1024)
    assert s.net_rx_human == "1.0KB"


def test_stats_net_tx_human():
    s = _make_stats(net_tx_bytes=2048)
    assert s.net_tx_human == "2.0KB"


# ---------------------------------------------------------------------------
# _parse_cpu_percent
# ---------------------------------------------------------------------------

def _cpu_raw(total=200, pretotal=100, system=2000, presystem=1000, percpu=None):
    if percpu is None:
        percpu = [50, 50]
    return {
        "cpu_stats": {
            "cpu_usage": {"total_usage": total, "percpu_usage": percpu},
            "system_cpu_usage": system,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": pretotal, "percpu_usage": percpu},
            "system_cpu_usage": presystem,
        },
    }


def test_parse_cpu_percent_basic():
    raw = _cpu_raw(total=200, pretotal=100, system=2000, presystem=1000, percpu=[50, 50])
    result = _parse_cpu_percent(raw)
    # cpu_delta=100, system_delta=1000, num_cpus=2 => 100/1000*2*100=20.0
    assert result == 20.0


def test_parse_cpu_percent_zero_system_delta():
    raw = _cpu_raw(system=1000, presystem=1000)
    assert _parse_cpu_percent(raw) == 0.0


def test_parse_cpu_percent_negative_cpu_delta():
    raw = _cpu_raw(total=50, pretotal=100, system=2000, presystem=1000)
    assert _parse_cpu_percent(raw) == 0.0


def test_parse_cpu_percent_no_percpu():
    raw = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 200},
            "system_cpu_usage": 2000,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 100},
            "system_cpu_usage": 1000,
        },
    }
    result = _parse_cpu_percent(raw)
    # num_cpus defaults to 1
    assert result == 10.0


# ---------------------------------------------------------------------------
# _parse_net_io
# ---------------------------------------------------------------------------

def test_parse_net_io_single_interface():
    raw = {"networks": {"eth0": {"rx_bytes": 1000, "tx_bytes": 500}}}
    rx, tx = _parse_net_io(raw)
    assert rx == 1000
    assert tx == 500


def test_parse_net_io_multiple_interfaces():
    raw = {
        "networks": {
            "eth0": {"rx_bytes": 1000, "tx_bytes": 500},
            "eth1": {"rx_bytes": 200, "tx_bytes": 100},
        }
    }
    rx, tx = _parse_net_io(raw)
    assert rx == 1200
    assert tx == 600


def test_parse_net_io_empty():
    assert _parse_net_io({}) == (0, 0)


# ---------------------------------------------------------------------------
# _parse_block_io
# ---------------------------------------------------------------------------

def test_parse_block_io_basic():
    raw = {
        "blkio_stats": {
            "io_service_bytes_recursive": [
                {"op": "Read", "value": 4096},
                {"op": "Write", "value": 8192},
                {"op": "Sync", "value": 100},
            ]
        }
    }
    r, w = _parse_block_io(raw)
    assert r == 4096
    assert w == 8192


def test_parse_block_io_empty():
    assert _parse_block_io({}) == (0, 0)


def test_parse_block_io_null_entries():
    raw = {"blkio_stats": {"io_service_bytes_recursive": None}}
    assert _parse_block_io(raw) == (0, 0)


# ---------------------------------------------------------------------------
# _state_color and _fmt_state
# ---------------------------------------------------------------------------

def test_state_color_running():
    assert _state_color("running") == "\033[32m"


def test_state_color_exited():
    assert _state_color("exited") == "\033[31m"


def test_state_color_paused():
    assert _state_color("paused") == "\033[33m"


def test_state_color_unknown():
    assert _state_color("unknown") == ""


def test_fmt_state_no_color():
    assert _fmt_state("running", use_color=False) == "running"


def test_fmt_state_with_color():
    result = _fmt_state("running", use_color=True)
    assert "\033[32m" in result
    assert "running" in result
    assert "\033[0m" in result


# ---------------------------------------------------------------------------
# _table_row
# ---------------------------------------------------------------------------

def test_table_row_basic():
    row = _table_row("A", "BB", "CCC", widths=[5, 5, 5])
    assert "A    " in row
    assert "BB   " in row
    assert "CCC  " in row


def test_table_row_exact_width():
    row = _table_row("hello", widths=[5])
    assert row == "hello"


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

def test_cmd_list_returns_zero_on_success(capsys):
    parser = build_parser()
    args = parser.parse_args(["list"])
    mock_client = MagicMock()
    mock_client.list_containers.return_value = [
        _make_container(state="running")
    ]
    result = cmd_list(args, mock_client)
    assert result == 0


def test_cmd_list_returns_one_on_runtime_error(capsys):
    parser = build_parser()
    args = parser.parse_args(["list"])
    mock_client = MagicMock()
    mock_client.list_containers.side_effect = RuntimeError("socket error")
    result = cmd_list(args, mock_client)
    assert result == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_cmd_list_no_containers_message(capsys):
    parser = build_parser()
    args = parser.parse_args(["list"])
    mock_client = MagicMock()
    mock_client.list_containers.return_value = []
    cmd_list(args, mock_client)
    captured = capsys.readouterr()
    assert "No containers found" in captured.out


# ---------------------------------------------------------------------------
# cmd_stats
# ---------------------------------------------------------------------------

def test_cmd_stats_container_not_found(capsys):
    parser = build_parser()
    args = parser.parse_args(["stats", "missing"])
    mock_client = MagicMock()
    mock_client.get_container.return_value = None
    result = cmd_stats(args, mock_client)
    assert result == 1
    assert "not found" in capsys.readouterr().err


def test_cmd_stats_container_not_running(capsys):
    parser = build_parser()
    args = parser.parse_args(["stats", "stopped_c"])
    mock_client = MagicMock()
    mock_client.get_container.return_value = _make_container(state="exited", name="stopped_c")
    result = cmd_stats(args, mock_client)
    assert result == 1
    assert "not running" in capsys.readouterr().err


def test_cmd_stats_success(capsys):
    parser = build_parser()
    args = parser.parse_args(["stats", "web"])
    mock_client = MagicMock()
    mock_client.get_container.return_value = _make_container(state="running", name="web")
    mock_client.get_stats.return_value = _make_stats()
    result = cmd_stats(args, mock_client)
    assert result == 0
    out = capsys.readouterr().out
    assert "web" in out
    assert "CPU" in out


def test_cmd_stats_runtime_error_on_get_stats(capsys):
    parser = build_parser()
    args = parser.parse_args(["stats", "web"])
    mock_client = MagicMock()
    mock_client.get_container.return_value = _make_container(state="running", name="web")
    mock_client.get_stats.side_effect = RuntimeError("stats unavailable")
    result = cmd_stats(args, mock_client)
    assert result == 1
    assert "error" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# cmd_ping
# ---------------------------------------------------------------------------

def test_cmd_ping_success(capsys):
    parser = build_parser()
    args = parser.parse_args(["ping"])
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    result = cmd_ping(args, mock_client)
    assert result == 0
    assert "reachable" in capsys.readouterr().out


def test_cmd_ping_failure(capsys):
    parser = build_parser()
    args = parser.parse_args(["ping"])
    mock_client = MagicMock()
    mock_client.ping.return_value = False
    result = cmd_ping(args, mock_client)
    assert result == 1
    assert "error" in capsys.readouterr().err
