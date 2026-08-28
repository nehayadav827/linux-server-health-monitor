#!/usr/bin/env python3
"""
Linux Server Health Monitor
----------------------------
A beginner-friendly command-line tool that checks the health of a Linux
machine by collecting system, resource, network, and process information.

Author: Neha Yadav
"""

import argparse
import platform
import socket
import time
from datetime import timedelta

import psutil

# ----------------------------------------------------------------------
# CONFIG: thresholds that decide when something becomes a WARNING
# ----------------------------------------------------------------------
CPU_THRESHOLD = 80
RAM_THRESHOLD = 80
DISK_THRESHOLD = 80


# ----------------------------------------------------------------------
# 1. SYSTEM INFORMATION
# ----------------------------------------------------------------------
def get_hostname():
    """Return the machine's hostname."""
    return socket.gethostname()


def get_os_info():
    """Return a short string describing the OS and kernel version."""
    # platform.system() -> 'Linux'
    # platform.release() -> kernel version, e.g. '5.15.0-91-generic'
    return f"{platform.system()} {platform.release()}"


def get_uptime():
    """Return system uptime as a human-readable string (e.g. '2 days, 5 hours')."""
    # psutil.boot_time() gives the boot time as a Unix timestamp.
    # Subtracting it from the current time gives seconds since boot.
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_delta = timedelta(seconds=uptime_seconds)

    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days} days, {hours} hours"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    else:
        return f"{minutes} minutes"


# ----------------------------------------------------------------------
# 2. RESOURCE USAGE
# ----------------------------------------------------------------------
def get_cpu_usage():
    """Return current CPU usage as a percentage (float)."""
    # interval=1 makes psutil measure CPU usage over 1 second instead of
    # instantly, which gives a far more accurate reading.
    return psutil.cpu_percent(interval=1)


def get_memory_usage():
    """Return current RAM usage as a percentage (float)."""
    memory = psutil.virtual_memory()
    return memory.percent


def get_disk_usage(path="/"):
    """Return current disk usage as a percentage (float) for the given path."""
    disk = psutil.disk_usage(path)
    return disk.percent


# ----------------------------------------------------------------------
# 3. NETWORK INFORMATION
# ----------------------------------------------------------------------
def bytes_to_readable(num_bytes):
    """Convert a raw byte count into a human-readable string (KB/MB/GB)."""
    # Standard binary-prefix conversion loop.
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def get_network_info():
    """Return total bytes sent and received across all interfaces."""
    net = psutil.net_io_counters()
    return net.bytes_sent, net.bytes_recv


def check_connectivity(host="8.8.8.8", port=53, timeout=3):
    """
    Check basic internet connectivity by opening a TCP socket to a
    known-reliable host (Google's public DNS server) on port 53 (DNS).
    This avoids needing to shell out to 'ping', which behaves
    inconsistently across systems and permissions.
    """
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except OSError:
        return False


# ----------------------------------------------------------------------
# 4. PROCESS MONITORING
# ----------------------------------------------------------------------
def get_top_processes(n=5, sample_time=0.5):
    """
    Return the top N processes sorted by CPU usage (descending).

    IMPORTANT: psutil.Process.cpu_percent() measures CPU usage *between
    two calls*. The very first call for a process always returns 0.0
    because there's no previous measurement to compare against. So we:
      1. Call cpu_percent() once on every process to set a baseline.
      2. Wait a short moment (sample_time).
      3. Call cpu_percent() again to get a real, meaningful reading.
    """
    procs = []
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            proc.cpu_percent(None)  # baseline call, discard the (0.0) result
            procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # A process can disappear between listing it and reading it,
            # or we may not have permission to see it. Skip those safely.
            continue

    time.sleep(sample_time)

    results = []
    for proc in procs:
        try:
            results.append({
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(None),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    results.sort(key=lambda p: p["cpu_percent"] or 0, reverse=True)
    return results[:n]


# ----------------------------------------------------------------------
# 5. HEALTH CHECKS
# ----------------------------------------------------------------------
def get_status(value, threshold):
    """Return 'WARNING' if value exceeds threshold, otherwise 'OK'."""
    return "WARNING" if value > threshold else "OK"


def get_overall_status(cpu, ram, disk):
    """Return the overall system status: HEALTHY or WARNING."""
    if cpu > CPU_THRESHOLD or ram > RAM_THRESHOLD or disk > DISK_THRESHOLD:
        return "WARNING"
    return "HEALTHY"


# ----------------------------------------------------------------------
# REPORT DISPLAY
# ----------------------------------------------------------------------
def print_report():
    """Collect all data points and print a full formatted health report."""
    hostname = get_hostname()
    os_info = get_os_info()
    uptime = get_uptime()

    cpu = get_cpu_usage()
    ram = get_memory_usage()
    disk = get_disk_usage()

    bytes_sent, bytes_recv = get_network_info()
    connected = check_connectivity()

    top_processes = get_top_processes()

    overall = get_overall_status(cpu, ram, disk)

    print("=" * 40)
    print("      LINUX SERVER HEALTH MONITOR")
    print("=" * 40)
    print()
    print(f"Hostname: {hostname}")
    print(f"OS:       {os_info}")
    print(f"Uptime:   {uptime}")
    print()
    print("SYSTEM RESOURCES")
    print("-" * 40)
    print(f"CPU Usage:       {cpu:>5.1f}%   [{get_status(cpu, CPU_THRESHOLD)}]")
    print(f"Memory Usage:    {ram:>5.1f}%   [{get_status(ram, RAM_THRESHOLD)}]")
    print(f"Disk Usage:      {disk:>5.1f}%   [{get_status(disk, DISK_THRESHOLD)}]")
    print()
    print("NETWORK")
    print("-" * 40)
    print(f"Bytes Sent:      {bytes_to_readable(bytes_sent)}")
    print(f"Bytes Received:  {bytes_to_readable(bytes_recv)}")
    print(f"Connectivity:    [{'OK' if connected else 'WARNING'}]")
    print()
    print("TOP PROCESSES (by CPU)")
    print("-" * 40)
    print(f"{'PID':<10}{'PROCESS':<18}{'CPU':>6}")
    for proc in top_processes:
        name = (proc["name"] or "unknown")[:16]
        cpu_pct = proc["cpu_percent"] or 0.0
        print(f"{proc['pid']:<10}{name:<18}{cpu_pct:>5.1f}%")
    print()
    print("=" * 40)
    print(f"Overall Status: {overall}")
    print("=" * 40)


def print_watch_line():
    """Print a single compact status line, used by --watch mode."""
    cpu = get_cpu_usage()
    ram = get_memory_usage()
    disk = get_disk_usage()
    overall = get_overall_status(cpu, ram, disk)
    timestamp = time.strftime("%H:%M:%S")
    print(f"{timestamp}  CPU: {cpu:>4.1f}%  RAM: {ram:>4.1f}%  "
          f"DISK: {disk:>4.1f}%  {overall}")


# ----------------------------------------------------------------------
# WATCH MODE
# ----------------------------------------------------------------------
def watch_mode(interval):
    """Repeatedly print a compact status line every `interval` seconds."""
    print(f"Watching system health every {interval} seconds. Press Ctrl+C to stop.\n")
    try:
        while True:
            print_watch_line()
            time.sleep(interval)
    except KeyboardInterrupt:
        # Catching this lets the user stop the loop with Ctrl+C cleanly,
        # instead of seeing a scary traceback.
        print("\nStopped watching.")


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Linux Server Health Monitor - check CPU, RAM, disk, "
                     "network, and process health from the command line."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously monitor health, refreshing every few seconds.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds for --watch mode (default: 5).",
    )

    args = parser.parse_args()

    if args.watch:
        watch_mode(args.interval)
    else:
        print_report()


if __name__ == "__main__":
    main()
