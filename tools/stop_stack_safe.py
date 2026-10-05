"""Stop only PID-file-identified stack processes, using Linux pidfds.

No port-based killing, process-group signals, escalation, or adoption of untracked
processes. A live identity mismatch retains the PID file and exits nonzero.
"""
import argparse
import os
from pathlib import Path
import re
import select
import signal
import stat

SPECS = (
    ('engainos_uvicorn', ('-m', 'uvicorn', 'tier1.engainos.engainos_server:app', '--host', '127.0.0.1', '--port', '8090')),
    ('launch_engine', ('-u', 'tier1/engainos/launch_engine.py')),
    ('sim_runtime', ('-u', '-m', 'tier2.godotsim.sim_runtime')),
)


def read_pidfile(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('PID file is not a regular file owned by this user')
        data = os.read(fd, 65)
        if len(data) > 64 or not re.fullmatch(rb'[1-9][0-9]*\n?', data):
            raise ValueError('invalid PID file')
        pid = int(data)
        if pid <= 1:
            raise ValueError('unsafe PID')
        return pid, data, (info.st_dev, info.st_ino)
    finally:
        os.close(fd)


def remove_unchanged(path, data, identity):
    info = path.lstat()
    if (info.st_dev, info.st_ino) != identity or path.read_bytes() != data:
        raise ValueError('PID file changed; retained')
    path.unlink()


def validate_process(pid, root, arguments):
    proc = Path('/proc') / str(pid)
    if proc.stat().st_uid != os.getuid():
        raise ValueError('process belongs to another user')
    if (proc / 'cwd').resolve(strict=True) != root:
        raise ValueError('process working directory is not this repository')
    argv = (proc / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
    argv = [os.fsdecode(part) for part in argv]
    if not argv or tuple(argv[1:]) != arguments:
        raise ValueError('process command does not match the launcher')
    # Compare executable identity, not just an easily forged argv[0].
    if not os.path.samefile(proc / 'exe', '/proc/self/exe'):
        raise ValueError('process executable is not this Python interpreter')


def stop_one(root, label, arguments):
    path = root / '.run' / (label + '.pid')
    try:
        pid, data, identity = read_pidfile(path)
    except FileNotFoundError:
        print(f'[SKIP] {label}: no PID file; no process adopted')
        return True
    fd = None
    try:
        try:
            fd = os.pidfd_open(pid)
        except ProcessLookupError:
            remove_unchanged(path, data, identity)
            print(f'[STALE] {label}: PID {pid} absent; removed stale PID file')
            return True
        poller = select.poll()
        poller.register(fd, select.POLLIN)
        if not poller.poll(0):
            validate_process(pid, root, arguments)
            # The pidfd pins the original process even if the numeric PID is reused.
            if not poller.poll(0):
                signal.pidfd_send_signal(fd, signal.SIGTERM)
                print(f'[STOP] {label}: SIGTERM sent to verified PID {pid}')
        if not poller.poll(10000):
            raise ValueError('shutdown timed out; no SIGKILL sent; PID file retained')
        remove_unchanged(path, data, identity)
        print(f'[OK] {label}: process exited; PID file removed')
        return True
    finally:
        if fd is not None:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
        print('[REFUSE] Linux pidfd support is required; nothing signalled')
        return 1
    rundir = root / '.run'
    if rundir.is_symlink():
        print('[REFUSE] .run is a symlink; nothing signalled')
        return 1
    ok = True
    for label, arguments in SPECS:
        try:
            ok = stop_one(root, label, arguments) and ok
        except (OSError, ValueError, OverflowError) as exc:
            print(f'[REFUSE] {label}: {exc}')
            ok = False
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
