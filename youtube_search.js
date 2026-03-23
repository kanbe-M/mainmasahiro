const { chromium } = require('/opt/node22/lib/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'ja-JP',
    timezoneId: 'Asia/Tokyo'
  });
  const page = await context.newPage();

  console.log('Navigating to YouTube search...');
  await page.goto('https://www.youtube.com/results?search_query=モラハラ+解説&sp=CAM%3D', {
    waitUntil: 'domcontentloaded',
    timeout: 30000
  });

  // Wait longer for dynamic content
  await page.waitForTimeout(5000);

  // Check what's on the page
  const pageTitle = await page.title();
  console.log('Page title:', pageTitle);

  const bodyText = await page.evaluate(() => document.body.innerHTML.substring(0, 500));
  console.log('Body preview:', bodyText);

  // Try different selectors
  const selectors = [
    'ytd-video-renderer',
    'ytd-compact-video-renderer',
    '#contents ytd-video-renderer',
    'div#contents',
    'ytd-search'
  ];

  for (const sel of selectors) {
    const count = await page.locator(sel).count();
    console.log(`Selector "${sel}": ${count} elements`);
  }

  await browser.close();
})();
