import { getLogger } from "./config/logger.ts";
import { UpdateClient } from "./output/client.ts";
import { WaterfallBuffer } from "./dsp/waterfall.ts";
import { Renderer } from "./views/renderer.ts";

const log = getLogger("dashboard.main");

const WS_URL = `ws://${window.location.hostname}:8765`;

function start(): void {
  log.info("Dashboard starting");
  
  const renderer = new Renderer();
  const waterfall = new WaterfallBuffer();
  const client = new UpdateClient(WS_URL);
  
  client.onStatus((status) => renderer.setStatus(status));
  
  client.onMessage((msg) => {
    waterfall.push([...msg.spectrum_dbfs]);
    renderer.renderSpectrum(msg);
    renderer.renderWaterfall(waterfall.rows);
    renderer.renderChannels(msg);
  });
  
  client.connect();
  log.info("Dashboard started");
}

document.addEventListener("DOMContentLoaded", start);
