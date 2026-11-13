export const TIMEZONE = "America/Bogota";
export const HAL_MODE = process.env.FM_HAL ?? "mock";
export const PORT = parseInt(process.env.FM_WEB_PORT ?? "8080", 10);
export const SOCKET_DIR = process.env.FM_SOCKET_DIR ?? "/run/fm";
export const REPORT_DIR = process.env.FM_REPORT_DIR ?? "/var/lib/fm/reports";
export const MAX_CONCURRENT = 8;
export const MAX_QUEUED = 64;
export const QUEUE_TIMEOUT_S = 30;
