# Technical Guide: Linux Server Health Monitor

This document explains **how the project works**, **why it was built this
way**, and **how to test it stage by stage**. It's meant to be your prep
material for explaining this project in a technical interview.

---

## 1. Folder Structure

```
linux-server-health-monitor/
│
├── monitor.py          # All monitoring logic lives here
├── requirements.txt     # Lists the one external dependency: psutil
├── README.md             # User-facing overview, install/usage instructions
├── TECHNICAL_GUIDE.md    # This file — deep explanation + testing steps
├── .gitignore             # Tells Git to ignore venv/, __pycache__, etc.
└── screenshots/            # Example terminal output, for the README/portfolio
```

It's a flat structure on purpose. There's no `src/` folder, no packages,
no config directory — for a project this size, that would add complexity
without adding value. A single, well-organized `monitor.py` is easier to
read, easier to explain, and still demonstrates good habits (small
functions, docstrings, comments explaining *why*, not just *what*).

---

## 2. How the Script Is Organized

`monitor.py` is organized into clearly labeled sections that mirror the
five things the project monitors:

| Section | Functions | Purpose |
|---|---|---|
| System Information | `get_hostname`, `get_os_info`, `get_uptime` | Identify the machine and how long it's been running |
| Resource Usage | `get_cpu_usage`, `get_memory_usage`, `get_disk_usage` | Core health metrics |
| Network Information | `get_network_info`, `check_connectivity`, `bytes_to_readable` | Network throughput + reachability |
| Process Monitoring | `get_top_processes` | Find what's consuming CPU |
| Health Checks | `get_status`, `get_overall_status` | Turn raw numbers into OK/WARNING/HEALTHY |
| Display | `print_report`, `print_watch_line` | Format everything for the terminal |
| Control Flow | `watch_mode`, `main` | Argument parsing and program entry point |

**Why this structure?** Each function does exactly one thing and returns a
value — none of them print anything directly (except the display
functions). This is a common and important design principle: **separate
data collection from data presentation**. It means you could later swap
the terminal output for a CSV log, a web dashboard, or a JSON API without
touching any of the collection logic. That separation is exactly the kind
of thing an interviewer is likely to ask about.

---

## 3. Key Python & Linux Concepts Explained

### `psutil.cpu_percent(interval=1)`
Calling this with `interval=1` tells psutil to measure CPU usage **over a
1-second window**, blocking for that second, then returning an accurate
percentage. Calling it with `interval=None` (the default) instead compares
against the *last* time it was called, which is faster but can be
inaccurate on the first call. This project uses `interval=1` for the main
report because accuracy matters more than speed for a single check.

### Why per-process CPU% needs two calls
`psutil.Process.cpu_percent()` works by measuring CPU time used **between
two calls**, not at a single instant (a CPU percentage is fundamentally
a *rate*, not a snapshot). The first call for any process always returns
`0.0` because there's nothing to compare it to yet. `get_top_processes()`
handles this correctly by:
1. Calling `cpu_percent(None)` once per process to set a baseline (and
   discarding that meaningless `0.0` result).
2. Sleeping briefly (`0.5` seconds).
3. Calling `cpu_percent(None)` again — now it can compute a real rate.

This is a real bug that shows up in almost every beginner psutil script
that lists "top processes," and understanding *why* it happens is a good
thing to be able to explain.

### `psutil.boot_time()` and uptime
`boot_time()` returns the system boot time as a Unix timestamp (seconds
since Jan 1, 1970). Subtracting it from `time.time()` (the current
timestamp) gives elapsed seconds since boot, which is then converted into
a `datetime.timedelta` for easy days/hours/minutes formatting.

### Connectivity check via raw TCP socket, not `ping`
The script opens a TCP connection to `8.8.8.8` (Google's public DNS
server) on port `53` (the standard DNS port) instead of shelling out to
the `ping` command. Reasons:
- `ping` requires raw ICMP sockets, which can need elevated permissions
  and behaves differently across environments (WSL, containers, cloud VMs).
- A plain TCP `connect()` call is simple, fast, uses only the standard
  library, and fails predictably (`OSError`) if there's no connectivity.

### `psutil.disk_usage("/")`
Reports usage of the filesystem mounted at `/` (the root filesystem) —
this is the Linux equivalent of checking "how full is the C: drive" on
Windows. `psutil.disk_usage()` wraps the same statistics as the Linux
`df` command.

### `argparse`
Python's standard library module for building command-line interfaces.
`--watch` is defined as a boolean flag (`action="store_true"`) — its mere
presence turns it on. `--interval` takes an integer value with a default,
so `python3 monitor.py --watch --interval 2` overrides the default 5
second refresh.

### Why no database or logging (yet)
The tool intentionally reads **live** data every run rather than storing
history. This keeps the mental model simple: run it, see the current
state, done. Persisting history (e.g., to CSV) is listed as a future
improvement in the README, and would be a natural "what would you add
next?" answer in an interview.

---

## 4. Testing Instructions (Stage by Stage)

Run these on your WSL Ubuntu terminal from inside the project folder.

### Stage 1 — Environment setup
```bash
python3 --version          # confirm Python 3 is installed
pip show psutil            # confirm psutil installed after requirements.txt
```
**Expected:** Python 3.x version printed; psutil shows a version number
(not "package not found").

### Stage 2 — Basic run (no arguments)
```bash
python3 monitor.py
```
**Expected:** A full report prints once and the program exits. Check that:
- Hostname and OS look correct for your machine
- CPU/RAM/Disk percentages look plausible (compare RAM% against `free -h`,
  disk% against `df -h /`)
- The `Overall Status` line matches what you'd expect given the numbers
  above it (any single WARNING metric should make overall status WARNING)

### Stage 3 — Trigger a WARNING deliberately
To see the WARNING path work (not just the happy path), temporarily lower
a threshold at the top of `monitor.py`, e.g.:
```python
CPU_THRESHOLD = 1
```
Run again:
```bash
python3 monitor.py
```
**Expected:** CPU line and Overall Status now show `WARNING`. Set the
threshold back to `80` afterward.

### Stage 4 — Top processes sanity check
```bash
python3 monitor.py
```
While it's running the 0.5s sample window, open another terminal and run:
```bash
stress --cpu 1 --timeout 3   # if 'stress' isn't installed: sudo apt install stress
```
**Expected:** the `stress` process (or a busy process you started) shows a
non-zero, plausible CPU% in the Top Processes list instead of all `0.0%`.

### Stage 5 — Connectivity check
```bash
python3 monitor.py
```
**Expected:** `Connectivity: [OK]` when you have internet access. Then
disconnect Wi-Fi/network (or disable WSL networking) and run again —
**expected:** `Connectivity: [WARNING]`.

### Stage 6 — Watch mode
```bash
python3 monitor.py --watch --interval 2
```
**Expected:** A new compact line prints every 2 seconds. Press `Ctrl+C`
and confirm you see `Stopped watching.` instead of a Python traceback —
this proves the `KeyboardInterrupt` handling works.

### Stage 7 — Argument errors
```bash
python3 monitor.py --interval abc
```
**Expected:** `argparse` itself rejects this with a clear usage error,
since `--interval` is typed as `int`. This is a good demonstration of
input validation without writing your own error-checking code.

---

## 5. Talking Points for the Interview

- "I separated data collection from display so the tool could later log
  to a file or serve an API without rewriting the monitoring logic."
- "I ran into a real bug where per-process CPU% always showed 0 — I
  learned that's because psutil measures CPU as a rate between two
  samples, not an instantaneous value, and fixed it with a baseline
  read + short sleep."
- "I used a raw TCP connect to check connectivity instead of shelling out
  to ping, to avoid permission issues with ICMP sockets."
- "The thresholds are simple constants right now — a natural next step
  would be making them configurable or logging historical data to spot
  trends instead of just point-in-time snapshots."
