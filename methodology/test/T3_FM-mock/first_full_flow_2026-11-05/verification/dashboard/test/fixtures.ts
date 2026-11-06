/**
 * Shared GV-5 fixture, loaded from the controlled vector
 * `verification/golden/gv5.json`.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import type { UpdateMessage } from "../../../src/dashboard/output/client.ts";

const here = dirname(fileURLToPath(import.meta.url));
const GV5_PATH = resolve(here, "../../golden/gv5.json");

/** The fixed Y8 message with n1 and n4 occupied (GV-5). */
export function gv5Message(): UpdateMessage {
  return JSON.parse(readFileSync(GV5_PATH, "utf8")) as UpdateMessage;
}
