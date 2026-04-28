const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const artifactsDir = path.join(process.cwd(), 'misc', 'e2e-artifacts');
  fs.mkdirSync(artifactsDir, { recursive: true });
  const logs = { console: [], responses: [], notes: [] };

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  page.on('console', msg => logs.console.push({ type: msg.type(), text: msg.text() }));
  page.on('response', async (res) => {
    const url = res.url();
    if (url.includes('/api/codes/create') || url.includes('/api/gemini') || url.includes('/api/ollama') || url.includes('/api/openrouter')) {
      let body = '';
      try { body = await res.text(); } catch {}
      logs.responses.push({ url, status: res.status(), body: body.slice(0, 1000) });
    }
  });
  page.on('dialog', async (dialog) => {
    if (dialog.type() === 'prompt') return dialog.accept('kelly');
    await dialog.accept();
  });

  await page.goto('http://localhost:8001');
  await page.fill('#login-username', 'admin');
  await page.fill('#login-password', '123');
  await page.click('#btn-login-submit');
  await page.waitForSelector('#main-content', { state: 'visible' });

  await page.click('#tab-taomabanve');
  await page.waitForSelector('#create-code-form', { state: 'visible' });
  await page.fill('#code-name', 'Nguoi test kho tinh');
  await page.fill('#employee-code', '123');
  await page.selectOption('#code-category', { index: 1 });
  await page.click('#btn-create-code-submit');
  await page.waitForTimeout(7000);

  const generatedVisible = await page.locator('#generated-code-container').isVisible().catch(() => false);
  let generatedCode = '';
  const genLoc = page.locator('#generated-code');
  if (await genLoc.count()) {
    generatedCode = ((await genLoc.first().textContent()) || '').trim();
  }
  logs.notes.push({ generatedVisible, generatedCode });

  const toastText = await page.locator('.toast-body').allTextContents().catch(() => []);
  logs.notes.push({ toastText });

  await page.screenshot({ path: path.join(artifactsDir, 'diag-code-tab.png'), fullPage: true });

  await page.click('#tab-ai');
  await page.waitForSelector('#chat-input-ai', { state: 'visible' });
  await page.fill('#chat-input-ai', 'Test AI response ngắn.');
  await page.click('#send-btn-ai');
  await page.waitForTimeout(12000);

  const aiMessages = await page.locator('#chat-messages-ai .message').count().catch(() => 0);
  const aiErrorCount = await page.locator('#chat-messages-ai .error-message').count().catch(() => 0);
  const aiLastText = await page.locator('#chat-messages-ai .message').last().innerText().catch(() => '');
  logs.notes.push({ aiMessages, aiErrorCount, aiLastText: aiLastText.slice(0, 400) });

  await page.screenshot({ path: path.join(artifactsDir, 'diag-ai-tab.png'), fullPage: true });

  const out = path.join(artifactsDir, 'diag-report.json');
  fs.writeFileSync(out, JSON.stringify(logs, null, 2));
  console.log(`DIAG_REPORT=${out}`);
  console.log(JSON.stringify(logs, null, 2));

  await browser.close();
})();
