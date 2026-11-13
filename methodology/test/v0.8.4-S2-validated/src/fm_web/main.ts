/**
 * fm_web — HTTP server on :8080, four screening views, read-only.
 */
import process from "node:process";
import { getLogger } from "./config/logger.ts";
import { HAL_MODE, PORT } from "./config/runtime.ts";
import { createServer } from "./output/http.ts";

const log = getLogger("fm_web.main");

async function main(): Promise<void> {
  log.info(`fm_web starting, HAL=${HAL_MODE}, port=${PORT}`);

  let dataPort;
  if (HAL_MODE === "real") {
    const { RealDataPort } = await import("./hal/real.ts");
    dataPort = new RealDataPort();
  } else {
    const { MockDataPort } = await import("./hal/mock.ts");
    dataPort = new MockDataPort();
  }

  const server = createServer(dataPort);
  server.listen(PORT, () => log.info(`fm_web listening on :${PORT}`));

  const shutdown = (): void => {
    log.info("fm_web shutting down");
    dataPort.close();
    server.close(() => process.exit(0));
  };
  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
