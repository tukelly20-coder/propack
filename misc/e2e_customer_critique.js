const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const baseUrl = 'http://localhost:8001';
  const artifactsDir = path.join(process.cwd(), 'misc', 'e2e-artifacts');
  fs.mkdirSync(artifactsDir, { recursive: true });

  const results = [];
  const notes = [];
  const testData = {
    stamp: Date.now(),
    projectName: '',
    createdCode: ''
  };

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  page.on('dialog', async (dialog) => {
    const type = dialog.type();
    const msg = dialog.message() || '';
    if (type === 'prompt') {
      const isCodeDelete = /xóa mã|delete code|mật khẩu|password/i.test(msg);
      await dialog.accept(isCodeDelete ? 'kelly' : '');
      return;
    }
    await dialog.accept();
  });

  async function screenshot(name) {
    const file = path.join(artifactsDir, `${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    return file;
  }

  async function wait(ms) {
    await page.waitForTimeout(ms);
  }

  async function runStep(name, fn) {
    try {
      await fn();
      results.push({ step: name, status: 'PASS' });
    } catch (error) {
      const shot = await screenshot(`error-${name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}`);
      results.push({ step: name, status: 'FAIL', error: String(error.message || error), screenshot: shot });
    }
  }

  async function clickIfVisible(selector) {
    const loc = page.locator(selector);
    if (await loc.count()) {
      const first = loc.first();
      if (await first.isVisible()) {
        await first.click();
        return true;
      }
    }
    return false;
  }

  await runStep('Open home page', async () => {
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('#login-modal', { timeout: 15000 });
    await screenshot('01-home-login');
  });

  await runStep('Login admin', async () => {
    await page.fill('#login-username', 'admin');
    await page.fill('#login-password', '123');
    await page.click('#btn-login-submit');
    await page.waitForSelector('#main-content', { state: 'visible', timeout: 20000 });
    await page.waitForSelector('#user-name', { timeout: 10000 });
    await screenshot('02-after-login');
  });

  await runStep('Switch language VI -> ZH -> VI', async () => {
    await page.click('#language-selector');
    await page.click('#lang-option-zh');
    await wait(1000);
    await page.click('#language-selector');
    await page.click('#lang-option-vi');
    await wait(1000);
    await screenshot('03-language-switch');
  });

  await runStep('Projects tab: load/search/create/delete', async () => {
    await page.click('#tab-projects');
    await page.waitForSelector('#projects-container', { state: 'visible', timeout: 20000 });
    await clickIfVisible('#btn-refresh-project');
    await wait(1500);

    testData.projectName = `E2E_SanPham_${testData.stamp}`;
    const customer = `E2E_Khach_${testData.stamp}`;

    await page.click('#btn-add-project');
    await page.waitForSelector('#project-modal.show', { timeout: 10000 });
    await page.fill('#field-khachhang', customer);
    await page.fill('#field-tensanpham', testData.projectName);
    await page.fill('#field-lienhe', 'Nguyen Test');
    await page.fill('#field-soluong', '10');
    await page.fill('#field-mapo', `PO-${testData.stamp}`);
    await page.fill('#field-tinhtrang', 'Moi tao');
    await page.click('#btn-save-project');
    await wait(2500);

    await page.fill('#search-input-project', testData.projectName);
    await page.keyboard.press('Enter');
    await wait(1500);

    const rows = page.locator('#projects-table-body tr');
    const rowCount = await rows.count();
    if (rowCount === 0) {
      throw new Error('Cannot find created project row after search');
    }

    const firstCheckbox = rows.first().locator('input[type="checkbox"]');
    if (await firstCheckbox.count()) {
      await firstCheckbox.check();
    } else {
      await rows.first().click();
    }

    await page.click('#btn-delete-project');
    await page.waitForSelector('#confirm-delete-modal-project.show', { timeout: 10000 });
    await page.click('#btn-confirm-delete-project');
    await wait(2000);
    await screenshot('04-projects-flow');
  });

  await runStep('Notices tab: load/filter/accept attempt', async () => {
    await page.click('#tab-notices');
    await page.waitForSelector('#notices-container', { state: 'visible', timeout: 20000 });
    await clickIfVisible('#btn-refresh-notice');
    await wait(1200);

    await page.selectOption('#filter-status-notice', { index: 0 }).catch(() => {});
    await page.selectOption('#filter-urgency-notice', { index: 0 }).catch(() => {});

    const noticeRows = page.locator('#notices-table-body tr');
    const noticeCount = await noticeRows.count();
    if (noticeCount > 0) {
      const cb = noticeRows.first().locator('input[type="checkbox"]');
      if (await cb.count()) {
        await cb.check();
        await clickIfVisible('#btn-accept-selected-notice');
        await wait(1200);
      }
    } else {
      notes.push('No notice rows available for accept flow.');
    }
    await screenshot('05-notices-flow');
  });

  await runStep('Create code tab: create/delete/export', async () => {
    await page.click('#tab-taomabanve');
    await page.waitForSelector('#create-code-form', { state: 'visible', timeout: 20000 });

    await page.fill('#code-name', 'Nguoi test kho tinh');
    await page.fill('#employee-code', '123');
    await page.selectOption('#code-category', { index: 1 });
    await page.click('#btn-create-code-submit');
    await page.waitForSelector('#generated-code-container', { state: 'visible', timeout: 20000 });

    const codeText = (await page.locator('#generated-code').textContent())?.trim() || '';
    testData.createdCode = codeText;

    if (codeText) {
      const btnDelete = page.locator(`#code-history-table-body button.btn-delete-history[data-code="${codeText}"]`);
      if (await btnDelete.count()) {
        await btnDelete.first().click();
        await wait(1800);
      } else {
        notes.push(`Created code ${codeText} but delete button by exact data-code not found.`);
      }
    } else {
      notes.push('Code creation returned empty code text.');
    }

    await clickIfVisible('#btn-export-history');
    await wait(1000);
    await screenshot('06-code-flow');
  });

  await runStep('Profile tab: edit profile + invalid password change', async () => {
    await page.click('#tab-profile');
    await page.waitForSelector('#field-username-profile', { state: 'visible', timeout: 20000 });

    const email = `qatest_${testData.stamp}@example.com`;
    await page.fill('#field-email-profile', email);
    await page.fill('#field-phone-profile', '0901234567');
    await page.click('#btn-save-profile');
    await wait(1500);

    await page.click('#btn-change-password-profile');
    await page.waitForSelector('#password-modal-profile.show', { timeout: 10000 });
    await page.fill('#current-password-profile', 'wrong-current');
    await page.fill('#new-password-profile', '123456');
    await page.fill('#confirm-password-profile', '123456');
    await page.click('#btn-confirm-change-password-profile');
    await wait(1200);
    await screenshot('07-profile-flow');
  });

  await runStep('AI tab: send one prompt', async () => {
    await page.click('#tab-ai');
    await page.waitForSelector('#chat-input-ai', { state: 'visible', timeout: 20000 });

    await page.fill('#chat-input-ai', 'Hãy tóm tắt ngắn 3 dòng về vai trò của quản lý dự án.');
    await page.click('#send-btn-ai');

    const aiMsg = page.locator('#chat-messages-ai .message.ai').last();
    await aiMsg.waitFor({ timeout: 25000 });
    await wait(1200);
    await screenshot('08-ai-flow');
  });

  await runStep('Mobile responsive smoke', async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#main-content', { timeout: 20000 });
    await screenshot('09-mobile-smoke');
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  await runStep('Logout', async () => {
    await page.click('#btn-logout');
    await page.waitForSelector('#login-modal', { state: 'visible', timeout: 15000 });
    await screenshot('10-logout');
  });

  const output = {
    timestamp: new Date().toISOString(),
    baseUrl,
    credentials: 'admin/123',
    testData,
    results,
    notes
  };

  const outPath = path.join(artifactsDir, 'customer-test-report.json');
  fs.writeFileSync(outPath, JSON.stringify(output, null, 2), 'utf8');

  await browser.close();

  console.log(`REPORT_FILE=${outPath}`);
  console.log(JSON.stringify(output, null, 2));
})();
