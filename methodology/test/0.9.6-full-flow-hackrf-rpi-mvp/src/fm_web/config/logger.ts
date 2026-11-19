/**
 * Cross-platform colored logger with caller context, the TypeScript twin of
 * `config/logger.py`.
 *
 * Self-contained: no dependency. Copy this file unchanged to
 * `src/<package>/config/logger.ts`. The timestamp timezone is read from
 * `TIMEZONE` in the sibling `config/runtime.ts`; it defaults to
 * `America/Bogota` and falls back to UTC when the zone is unknown.
 *
 * Node: `[YYYY-MM-DD HH:MM:SS.mmm] LEVEL name.funcName message` on stderr,
 * ANSI colours unless `NO_COLOR`, forced by `FORCE_COLOR`, else only on a TTY.
 * Browser: `[YYYY-MM-DD HH:MM:SS.mmm] LEVEL name message` on the console,
 * with the same hues through `%c` CSS.
 *
 * @example
 * import { getLogger } from "./config/logger.ts";
 * const log = getLogger("dashboard.main");
 * log.info("started");
 */

import * as runtime from "./runtime.ts";

export type Level = "DEBUG" | "INFO" | "WARNING" | "ERROR";

export interface Logger {
  debug(message: string): void;
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
}

interface NodeProcessLike {
  env: Record<string, string | undefined>;
  stderr?: { isTTY?: boolean; write(chunk: string): boolean };
}

const RANK: Record<Level, number> = { DEBUG: 10, INFO: 20, WARNING: 30, ERROR: 40 };

const COLORS: Record<Level, string> = {
  DEBUG: "\x1b[90m",
  INFO: "\x1b[35m",
  WARNING: "\x1b[33m",
  ERROR: "\x1b[31m",
};
const RESET = "\x1b[0m";
const DIM = "\x1b[2m";

const CSS: Record<Level, string> = {
  DEBUG: "color: #808080",
  INFO: "color: #c000c0",
  WARNING: "color: #c0a000",
  ERROR: "color: #c00000",
};
const CSS_DIM = "opacity: 0.6";

const CONSOLE_METHOD: Record<Level, "debug" | "info" | "warn" | "error"> = {
  DEBUG: "debug",
  INFO: "info",
  WARNING: "warn",
  ERROR: "error",
};

const DEFAULT_TIMEZONE = "America/Bogota";
const nodeProcess = (globalThis as { process?: NodeProcessLike }).process;
const isNode = nodeProcess?.stderr !== undefined;
const loggers = new Map<string, Logger>();

/** Build the `YYYY-MM-DD HH:MM:SS` formatter, with the UTC fallback. */
function makeFormatter(): Intl.DateTimeFormat {
  const configured = (runtime as { TIMEZONE?: string }).TIMEZONE || DEFAULT_TIMEZONE;
  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  };
  try {
    return new Intl.DateTimeFormat("en-CA", { ...options, timeZone: configured });
  } catch {
    return new Intl.DateTimeFormat("en-CA", { ...options, timeZone: "UTC" });
  }
}

const formatter = makeFormatter();

/** Format a date with millisecond precision in the log timezone. */
function formatTimestamp(date: Date): string {
  const parts: Record<string, string> = {};
  for (const part of formatter.formatToParts(date)) {
    parts[part.type] = part.value;
  }
  const millis = String(date.getMilliseconds()).padStart(3, "0");
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}.${millis}`;
}

/** Same rule as the Python logger: NO_COLOR, FORCE_COLOR, then the TTY check. */
function supportsColor(): boolean {
  if (!nodeProcess) return false;
  if (nodeProcess.env.NO_COLOR) return false;
  if (nodeProcess.env.FORCE_COLOR) return true;
  // Node enables virtual-terminal processing on Windows consoles by itself.
  return nodeProcess.stderr?.isTTY === true;
}

const ownUrl = import.meta.url;

/** Best-effort caller function name from the stack trace, like `%(funcName)s`. */
function callerName(): string {
  const stack = new Error().stack ?? "";
  for (const line of stack.split("\n").slice(1)) {
    if (line.includes(ownUrl)) continue;
    const match = /^\s*at\s+(?:async\s+)?(?:new\s+)?([^\s(]+)\s+\(/.exec(line);
    if (!match) return "<module>";
    const name = match[1].split(".").pop() ?? "";
    return name === "" || name === "<anonymous>" ? "<module>" : name;
  }
  return "<module>";
}

/**
 * Get a named logger.
 *
 * @param name - Logger name, usually `<package>.<module>`.
 * @param level - Lowest level emitted; `DEBUG` by default.
 * @returns The cached logger for `name`.
 */
export function getLogger(name: string, level: Level = "DEBUG"): Logger {
  const cached = loggers.get(name);
  if (cached) return cached;

  const useColor = supportsColor();

  const emit = (lvl: Level, message: string): void => {
    if (RANK[lvl] < RANK[level]) return;
    const stamp = formatTimestamp(new Date());
    if (isNode) {
      const label = useColor ? `${COLORS[lvl]}${lvl}${RESET}` : lvl;
      const who = useColor ? `${DIM}${name}${RESET}` : name;
      nodeProcess?.stderr?.write(`[${stamp}] ${label} ${who}.${callerName()} ${message}\n`);
      return;
    }
    console[CONSOLE_METHOD[lvl]](`[${stamp}] %c${lvl}%c %c${name}%c ${message}`, CSS[lvl], "", CSS_DIM, "");
  };

  const logger: Logger = {
    debug: (message) => emit("DEBUG", message),
    info: (message) => emit("INFO", message),
    warn: (message) => emit("WARNING", message),
    error: (message) => emit("ERROR", message),
  };
  loggers.set(name, logger);
  return logger;
}
