const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const [archiveUrl, fixtureUrl] = process.argv.slice(2);
const order = ['S0', 'G0', 'S1', 'G1', 'S2', 'G2', 'S3', 'G3'];

async function open(page, url) {
  await page.goto(url);
  await page.locator('.flow-stage').last().waitFor();
  assert.deepEqual(await page.locator('.stage-id').allTextContents(), order);
  await page.getByRole('button', { name: /S3 test run/ }).click();
  await page.locator('.markdown-body').waitFor();
  await page.getByRole('button', { name: /Verified Prototype/ }).click();
  await page.getByRole('heading', { name: /^Verified Prototype/ }).last().waitFor();
  await page.getByRole('button', { name: 'Telemetry & VL-2', exact: true }).click();
  await page.getByText('Current G3 evidence', { exact: true }).waitFor();
}

async function archive(page) {
  await open(page, archiveUrl);
  await page.getByText(/^VL-2: NO EVIDENCE/).waitFor();
  await page.getByText('No telemetry samples recorded').waitFor();
  await page.getByText('No v2 measurement.json records').waitFor();
  await page.getByText('63.35 °C', { exact: true }).waitFor();
  await page.getByText('Manually recorded target readings').waitFor();
  assert.equal(await page.locator('canvas').count(), 0);
  await page.getByText('PATH-006', { exact: true }).waitFor();
  await page.getByText(/^INCONCLUSIVE \(needs/).first().waitFor();
  await page.getByRole('button', { name: /vitest_vl1.txt/ }).first().click();
  await page.locator('.test-log-content pre').waitFor();
  assert.ok((await page.locator('.test-log-content pre').innerText()).trim());
}

async function fixture(page) {
  await open(page, fixtureUrl);
  await page.getByText(/^VALIDATED \(VL-2.*none/).waitFor();
  await page.getByText('pump_guard', { exact: true }).waitFor();
  assert.match(await page.getByText('VL-1 PASS; VL-2 BLOCKED', { exact: true }).getAttribute('class'), /\bfail\b/);
  await page.getByText('INCONCLUSIVE', { exact: true }).first().waitFor();
  await page.getByText('12 kPa', { exact: true }).waitFor();
  await page.getByText('at most 15 kPa', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Source record' }).click();
  assert.match(await page.locator('.test-log-content pre').innerText(), /SYS-013/);
  await page.getByRole('button', { name: 'Close', exact: true }).click();

  const canvas = page.locator('.uplot canvas');
  const plot = page.locator('.u-over');
  const legend = page.locator('.u-legend .u-value').last();
  await canvas.scrollIntoViewIfNeeded();
  await page.getByText(/9 measured points · 10 samples · UTC\/local time/).waitFor();
  await page.getByText('fixture gap').waitFor();
  const width = (await canvas.boundingBox()).width;
  await page.setViewportSize({ width: 1100, height: 960 });
  await page.waitForFunction(old => document.querySelector('.uplot canvas').getBoundingClientRect().width < old, width);
  const bounds = await plot.boundingBox();
  const point = fraction => ({ x: bounds.x + bounds.width * fraction, y: bounds.y + bounds.height / 2 });
  const hover = async fraction => {
    const { x, y } = point(fraction);
    await page.mouse.move(x, y);
  };
  const waitLegend = value => page.waitForFunction(text =>
    [...document.querySelectorAll('.u-legend .u-value')].at(-1)?.textContent === text, value);

  // Assert that the rendered series has ink on each side and none at the gap.
  const ink = await canvas.evaluate(element => {
    const context = element.getContext('2d');
    const { width, height } = element;
    const pixels = context.getImageData(0, 0, width, height).data;
    const over = element.closest('.uplot').querySelector('.u-over').getBoundingClientRect();
    const surface = element.getBoundingClientRect();
    const column = fraction => Math.round((over.left - surface.left + over.width * fraction) * width / surface.width);
    const cyan = x => {
      for (let y = 0; y < height; y++) {
        const i = (y * width + x) * 4;
        if (pixels[i + 3] && pixels[i + 1] > 170 && pixels[i + 1] - pixels[i] > 50 && pixels[i + 2] > 170) return true;
      }
      return false;
    };
    return [cyan(column(2/9)), cyan(column(4/9)), cyan(column(7/9))];
  });
  assert.deepEqual(ink, [true, false, true]);
  await hover(2/9);
  await waitLegend('18 %');
  assert.equal(await page.locator('.u-cursor-x').count(), 1);
  await hover(4/9);
  await waitLegend('—');

  const from = point(0.18), to = point(0.8);
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move(to.x, to.y, { steps: 12 });
  await page.mouse.up();
  await hover(2/9);
  await page.waitForFunction(() => {
    const value = [...document.querySelectorAll('.u-legend .u-value')].at(-1)?.textContent;
    return value !== '18 %' && /^\d+ %$/.test(value);
  });
  await page.getByRole('button', { name: 'Reset zoom' }).click();
  await hover(2/9);
  await waitLegend('18 %');

  await page.getByRole('button', { name: /pytest_vl1.txt/ }).click();
  assert.equal(await page.locator('.test-log-content pre').innerText(), '02_pump captured result');
  await page.getByRole('combobox', { name: 'Cycle' }).selectOption('02_pump_retry');
  await page.getByText('19 kPa', { exact: true }).waitFor();
  assert.equal(await page.getByText('12 kPa', { exact: true }).count(), 0);
  assert.equal(await page.locator('.test-log-content').count(), 0);
  await page.getByText('No current G3 Verified Prototype').waitFor();
  await page.getByText(/9 measured points · 10 samples · sample index/).waitFor();
  await page.getByRole('button', { name: /pytest_vl1.txt/ }).click();
  assert.equal(await page.locator('.test-log-content pre').innerText(), '02_pump_retry captured result');
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  assert.equal(await page.locator('.flow-line').getByText('Not started').count(), 7);
  assert.equal(await page.getByRole('option', { name: '02_pump · active' }).count(), 1);
}

(async () => {
  const browser = await chromium.launch();
  try {
    for (const [name, check] of [['archive', archive], ['fixture', fixture]]) {
      const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
      page.setDefaultTimeout(5000);
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await check(page);
      assert.deepEqual(errors, []);
      await page.close();
      console.log(`${name}: PASS`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
