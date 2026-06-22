# Testing Guide

## Running Tests

Install dependencies including test tools:

```bash
pip install -e ".[test]"
```

Or if `[test]` is not defined in `pyproject.toml`, install pytest:

```bash
pip install pytest pytest-cov
```

## Running Test Suite

Run all tests:

```bash
pytest tests/
```

Run with verbose output:

```bash
pytest -v tests/
```

Run with coverage report:

```bash
pytest --cov=src --cov-report=html tests/
```

## Test Organization

Tests are in `tests/test_dockwatch.py` and cover:

### CLI Parsing (`build_parser`)

- `test_build_parser_returns_parser` — parser creation
- `test_build_parser_list_subcommand` — list command parsing
- `test_build_parser_list_alias_ls` — ls alias
- `test_build_parser_list_all_flag` — --all flag
- `test_build_parser_stats_subcommand` — stats command with container argument
- `test_build_parser_watch_defaults` — watch defaults (interval=3)
- `test_build_parser_watch_interval` — custom refresh interval
- `test_build_parser_ping_subcommand` — ping command
- `test_build_parser_custom_socket` — --socket flag
- `test_build_parser_no_color_flag` — --no-color flag
- `test_build_parser_missing_subcommand_exits` — exits without command
- `test_build_parser_unknown_subcommand_exits` — exits on invalid command
- `test_build_parser_stats_missing_positional_exits` — stats requires container arg

### Container Info (`ContainerInfo`)

- `test_container_info_short_id` — 12-char ID truncation
- `test_container_info_is_running_true` — running state detection
- `test_container_info_is_running_false` — stopped state detection
- `test_container_info_is_running_case_insensitive` — case-insensitive state check
- `test_container_info_uptime_seconds_non_negative` — uptime calculation
- `test_container_info_uptime_human_seconds` — format seconds as "Ns"
- `test_container_info_uptime_human_minutes` — format minutes as "Nm Ns"
- `test_container_info_uptime_human_hours` — format hours as "Nh Nm"
- `test_container_info_no_ports` — handle empty port list

### Container Stats (`ContainerStats`)

- `test_stats_mem_percent` — memory percentage calculation
- `test_stats_mem_percent_zero_limit` — handle zero memory limit
- `test_stats_human_bytes` — human-readable bytes
- `test_stats_human_kilobytes` — human-readable KB
- `test_stats_human_megabytes` — human-readable MB
- `test_stats_human_gigabytes` — human-readable GB
- `test_stats_mem_usage_human` — format memory usage
- `test_stats_net_rx_human` — format network receive
- `test_stats_net_tx_human` — format network transmit

### CPU Parsing (`_parse_cpu_percent`)

- `test_parse_cpu_percent_basic` — calculate CPU percentage
- `test_parse_cpu_percent_zero_system_delta` — handle no CPU change
- `test_parse_cpu_percent_negative_cpu_delta` — handle negative delta
- `test_parse_cpu_percent_no_percpu` — default to 1 CPU if missing

### Network I/O Parsing (`_parse_net_io`)

- `test_parse_net_io_single_interface` — sum single interface
- `test_parse_net_io_multiple_interfaces` — sum multiple interfaces
- `test_parse_net_io_empty` — handle empty networks

### Block I/O Parsing (`_parse_block_io`)

- `test_parse_block_io_basic` — separate read and write
- `test_parse_block_io_empty` — handle missing stats
- `test_parse_block_io_null_entries` — handle null entries

### Formatting

- `test_state_color_running` — green color code for running
- `test_state_color_exited` — red color code for exited
- `test_state_color_paused` — yellow color code for paused
- `test_state_color_unknown` — empty string for unknown states
- `test_fmt_state_no_color` — plain text without color flag
- `test_fmt_state_with_color` — ANSI codes with color flag
- `test_table_row_basic` — column alignment and spacing
- `test_table_row_exact_width` — exact width matching

### Commands

#### List (`cmd_list`)

- `test_cmd_list_returns_zero_on_success` — exit code 0 on success
- `test_cmd_list_returns_one_on_runtime_error` — exit code 1 on error
- `test_cmd_list_no_containers_message` — message when no containers exist

#### Stats (`cmd_stats`)

- `test_cmd_stats_container_not_found` — error if container missing
- `test_cmd_stats_container_not_running` — error if container not running
- `test_cmd_stats_success` — display stats for running container
- `test_cmd_stats_runtime_error_on_get_stats` — error handling in stats fetch

#### Ping (`cmd_ping`)

- `test_cmd_ping_success` — report reachable daemon
- `test_cmd_ping_failure` — report unreachable daemon

## Running Specific Tests

Run a single test function:

```bash
pytest tests/test_dockwatch.py::test_build_parser_returns_parser
```

Run tests matching a pattern:

```bash
pytest -k "cmd_list" tests/
```

Run only parsing tests:

```bash
pytest -k "parse" tests/
```

## Test Utilities

Tests use mock objects to avoid requiring a real Docker daemon:

```python
from unittest.mock import MagicMock

mock_client = MagicMock()
mock_client.list_containers.return_value = [...]
```

Container and stats fixtures are defined as helper functions:

```python
def _make_container(**overrides) -> ContainerInfo:
    # Creates a sample container with defaults

def _make_stats(**overrides) -> ContainerStats:
    # Creates a sample stats object with defaults
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[test]"
      - run: pytest --cov=src tests/
```
