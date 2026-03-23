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
  await page.goto('https://www.youtube.com/results?search_query=%E3%83%A2%E3%83%A9%E3%83%8F%E3%83%A9+%E8%A7%A3%E8%AA%AC&sp=CAM%253D', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });

  // Wait for dynamic content to load
  await page.waitForTimeout(5000);

  // Try to accept cookies if prompted
  try {
    const acceptBtn = page.locator('button:has-text("Accept"), button:has-text("同意"), [aria-label="Accept the use of cookies"]');
    if (await acceptBtn.count() > 0) {
      await acceptBtn.first().click();
      await page.waitForTimeout(2000);
    }
  } catch (e) {}

  // Scroll to load more results
  for (let i = 0; i < 3; i++) {
    await page.evaluate(() => window.scrollBy(0, 2000));
    await page.waitForTimeout(2000);
  }

  // Extract video data
  const videos = await page.evaluate(() => {
    const results = [];
    const videoElements = document.querySelectorAll('ytd-video-renderer');

    videoElements.forEach((el, index) => {
      if (index >= 20) return;

      // Title
      const titleEl = el.querySelector('#video-title, h3 a#video-title, a#video-title yt-formatted-string');
      const title = titleEl ? titleEl.textContent.trim() : '';

      // Channel name
      const channelEl = el.querySelector('#channel-name a, .ytd-channel-name a, #channel-info a');
      const channel = channelEl ? channelEl.textContent.trim() : '';

      // View count and date from metadata line
      const metaItems = el.querySelectorAll('#metadata-line span.ytd-video-meta-block');
      let views = '';
      let date = '';
      metaItems.forEach((span, i) => {
        const text = span.textContent.trim();
        if (text.includes('回視聴') || text.includes('views') || text.includes('万回') || text.includes('千回')) {
          views = text;
        } else if (text.includes('前') || text.includes('ago') || text.includes('年') || text.includes('月') || text.includes('日')) {
          date = text;
        }
      });

      if (title) {
        results.push({ index: index + 1, title, channel, views, date });
      }
    });

    return results;
  });

  console.log(JSON.stringify(videos, null, 2));
  console.log('TOTAL_COUNT:' + videos.length);

  await browser.close();
})();
