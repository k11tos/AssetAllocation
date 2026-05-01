# Operations Guide

Practical runbook for day-to-day execution, reporting, and result inspection.

## 1) Execution paths

### Scheduled path (`main.py`)
Use this for regular/scheduled runs:

```bash
uv run python main.py
```

What it does:
- validates configuration
- runs scheduled strategies through shared orchestration (`run_selected_strategies(..., "main")`)
- compares with previous scheduled snapshot (if `outputs/latest.json` exists)
- prints a compact scheduled diff summary when changes exist
- persists both:
  - latest snapshot: `outputs/latest.json`
  - timestamped history snapshot: `outputs/history/YYYYMMDD_HHMMSS.json`

### Manual path (`asset-cli`)
Use this for ad-hoc/operator workflows:

```bash
uv run asset-cli
```

Common operator actions:
- run selected strategy: `uv run asset-cli --strategy haa`
- save current run to JSON: `uv run asset-cli --strategy haa --save-json outputs/manual_haa.json`
- compare current run vs saved snapshot: `uv run asset-cli --strategy haa --compare-json outputs/latest.json`

## 2) Shared orchestration model

Both entrypoints delegate strategy execution to the same orchestration layer (`strategy_runner.py`).

- Scheduled path: `main.py` -> orchestration with context `"main"`
- CLI path: `cli.py` (`asset-cli`) -> orchestration with context `"cli"`

This keeps strategy dispatch behavior consistent while allowing different output/reporting behavior per entrypoint.

## 3) Result storage layout

Scheduled persistence is centered on `outputs/`:

- `outputs/latest.json`
  - most recent scheduled snapshot
  - used as baseline for the next scheduled diff
- `outputs/history/*.json`
  - immutable timestamped snapshots
  - used for audit/history review

JSON payload shape:

```json
{
  "timestamp": "...",
  "strategies": {
    "HAA": {"...": 0.0},
    "KAW": {"...": 0.0}
  }
}
```

## 4) Compare/diff behavior

### Scheduled (`main.py`)
- loads prior baseline from `outputs/latest.json` (if present)
- creates full diff summary for logs
- creates compact diff summary for operator-facing report output
- then saves new `latest.json` and history snapshot

### CLI (`asset-cli --compare-json`)
- compares current run result with the provided JSON file
- prints full text diff summary in text output mode
- does **not** auto-update scheduled storage unless `--save-json` is used

## 5) Compact diff reporting in the flow

Compact diff reporting is designed for scheduled/regular operational visibility:

- produced during scheduled persistence flow
- intended as concise “what changed since last run” signal
- complements (not replaces) the full diff summary logged internally

## 6) Host-side monthly scheduling with systemd (Raspberry Pi)

Use host-level systemd timer scheduling for production monthly runs. GitHub Actions only prepares and updates image availability on the host.

Example files are provided in `deploy/systemd/`:
- `asset-allocation-monthly.service`
- `asset-allocation-monthly.timer`

Install on Raspberry Pi host (adjust paths as needed):

```bash
sudo cp deploy/systemd/asset-allocation-monthly.service /etc/systemd/system/
sudo cp deploy/systemd/asset-allocation-monthly.timer /etc/systemd/system/
```

Then:

```bash
# edit WorkingDirectory in the service if needed
sudo systemctl daemon-reload
sudo systemctl enable --now asset-allocation-monthly.timer
```

Schedule details:
- `OnCalendar=*-*-01 08:00:00`
- local host timezone
- `Persistent=true` (runs once after boot if a scheduled run was missed while offline)

Useful checks:

```bash
systemctl list-timers asset-allocation-monthly.timer
systemctl status asset-allocation-monthly.timer
journalctl -u asset-allocation-monthly.service -n 100 --no-pager
```

## 7) Inspect history and snapshots from CLI

```bash
# list latest 10 snapshots from outputs/history
uv run asset-cli --history

# list latest 5 snapshots
uv run asset-cli --history 5

# show one snapshot in human-readable detail
uv run asset-cli --show-history outputs/history/20260101_000000.json

# show one snapshot as raw JSON
uv run asset-cli --show-history outputs/history/20260101_000000.json --output json
```

## 8) Troubleshooting (quick)

### Expected output is missing
1. Confirm you used the right entrypoint:
   - scheduled persistence: `uv run python main.py`
   - ad-hoc CLI run: `uv run asset-cli ...`
2. Check whether `outputs/latest.json` and `outputs/history/` were created/updated.
3. Re-run with CLI verbose logs where useful:
   - `uv run asset-cli --verbose --strategy haa`

### Need to inspect what was saved previously
- list snapshots: `uv run asset-cli --history`
- inspect one snapshot: `uv run asset-cli --show-history <snapshot-path>`
- compare current run to a saved snapshot: `uv run asset-cli --compare-json <snapshot-path>`

### Verify CI/tests locally before/after operations changes
```bash
uv run python -m pytest
```

(Repository CI for pull requests also runs compile/import checks plus pytest.)

### Twelve Data operations
- Env vars: `PRICE_PROVIDER=twelvedata`, `TWELVEDATA_API_KEY=<key>`.
- Compare providers by running HAA debug report twice (Yahoo and Twelve Data) and diffing TIP diagnostics.
