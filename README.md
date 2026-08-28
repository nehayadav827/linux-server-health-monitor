# Linux Server Health Monitor

A simple command-line tool, written in Python, that checks the health of a Linux
machine — CPU, memory, disk, network, and top processes — and reports whether
the system is **HEALTHY** or needs a **WARNING**.

## Why I Built This

I built this project to demonstrate practical, hands-on skills relevant to a
**Data Center Technician** role: Linux systems, basic scripting, resource
monitoring, and troubleshooting. Rather than build something overly complex,
I wanted a small tool I could fully understand, explain line-by-line, and
extend later.

## Features

- Reports hostname, OS, and system uptime
- Reports CPU, RAM, and disk usage as percentages
- Flags any resource above 80% usage as a `WARNING`
- Reports network bytes sent/received and basic internet connectivity
- Lists the top 5 processes by CPU usage
- `--watch` mode: continuously refreshes health status every few seconds
- Gives one clear overall status: `HEALTHY` or `WARNING`

## Technologies Used

- **Python 3** — core language
- **[psutil](https://psutil.readthedocs.io/)** — cross-platform library for
  reading system/process/network stats
- **argparse** — standard library module for command-line arguments
- **socket** — standard library module used for the connectivity check
- Standard Linux environment (developed and tested on Ubuntu via WSL)

No web framework, database, Docker, or cloud services are used — this is a
local command-line tool by design.

## Installation

These steps assume Ubuntu on WSL (or any Ubuntu/Debian-based Linux).

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/linux-server-health-monitor.git
cd linux-server-health-monitor

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Usage

Run a single health check:

```bash
python3 monitor.py
```

Run in continuous watch mode (refreshes every 5 seconds by default):

```bash
python3 monitor.py --watch
```

Run in watch mode with a custom refresh interval (e.g. every 2 seconds):

```bash
python3 monitor.py --watch --interval 2
```

Press `Ctrl+C` to stop watch mode.

## Example Output

**Single report:**

```
========================================
      LINUX SERVER HEALTH MONITOR
========================================

Hostname: ubuntu-server
OS:       Linux 5.15.0-91-generic
Uptime:   2 days, 5 hours

SYSTEM RESOURCES
----------------------------------------
CPU Usage:         42.0%   [OK]
Memory Usage:      64.0%   [OK]
Disk Usage:        87.0%   [WARNING]

NETWORK
----------------------------------------
Bytes Sent:      1.24 GB
Bytes Received:  3.82 GB
Connectivity:    [OK]

TOP PROCESSES (by CPU)
----------------------------------------
PID       PROCESS              CPU
1240      chrome              18.2%
3021      python3              7.4%
891       systemd              2.1%

========================================
Overall Status: WARNING
========================================
```

**Watch mode:**

```
15:30:02  CPU: 34.0%  RAM: 61.0%  DISK: 72.0%  HEALTHY
15:30:07  CPU: 39.0%  RAM: 62.0%  DISK: 72.0%  HEALTHY
15:30:12  CPU: 88.0%  RAM: 63.0%  DISK: 72.0%  WARNING
```

## Architecture / Workflow

1. **Collect** — small, focused functions each gather one piece of data
   (CPU %, RAM %, disk %, network counters, connectivity, top processes)
   using `psutil` and the standard library.
2. **Evaluate** — each resource value is compared against a threshold
   (default 80%) to decide `OK` vs `WARNING`.
3. **Report** — the results are formatted and printed either as a full
   report (default) or a compact one-line summary (`--watch` mode).

There is no persistent state, no database, and no background service — the
script reads live system data each time it runs, which keeps the project
simple and easy to reason about.

## What I Learned

- How to read live system metrics (CPU, memory, disk, network) in Python
  using `psutil`
- Why `cpu_percent()` needs two measurements over time to be meaningful,
  and how to sample it correctly for both the whole system and individual
  processes
- How to build a command-line interface with `argparse`
- How to structure a small Python project so each function has a single,
  clear responsibility
- Basic networking concepts: checking connectivity via a raw TCP socket
  instead of shelling out to `ping`

## Possible Future Improvements

- Log historical results to a CSV file for trend analysis
- Send an alert (email/Slack) when status changes to `WARNING`
- Add configurable thresholds via a config file or command-line flags
- Add per-core CPU breakdown and per-disk-partition usage
- Package as a proper CLI tool with `pip install -e .`

## Project Structure

```
linux-server-health-monitor/
│
├── monitor.py          # Main script — all monitoring logic
├── requirements.txt     # Python dependencies (psutil)
├── README.md            # This file
├── .gitignore
└── screenshots/          # Example output screenshots
```
