"""Set a controlling terminal after Popen's setsid, then become the local CLI."""

import os
import sys


def main() -> int:
    if not sys.platform.startswith("linux") or len(sys.argv) < 2:
        print("A local terminal requires Linux/WSL and a command.", file=sys.stderr)
        return 127

    import fcntl
    import termios

    try:
        # All three standard descriptors already refer to the inherited slave.
        # The inherited descriptor prevents an early master-side EIO race.
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
        os.tcsetpgrp(0, os.getpgrp())
        os.execvpe(sys.argv[1], sys.argv[1:], os.environ)
    except OSError as error:
        print(f"Cannot execute local terminal command: {error}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
