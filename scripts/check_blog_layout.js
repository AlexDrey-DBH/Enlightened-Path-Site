const { chromium } = require("playwright");
const path = require("path");
const { pathToFileURL } = require("url");

const pages = process.argv.slice(2);
if (!pages.length) {
  console.error("Pass one or more HTML files.");
  process.exit(2);
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });
  let failed = false;
  for (const file of pages) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: "domcontentloaded" });
    const result = await page.evaluate(() => {
      const selectors = [
        ".legacy-article-hero-inner",
        ".legacy-article-heading",
        ".legacy-article-layout",
        ".legacy-article-body",
      ];
      const boxes = Object.fromEntries(
        selectors.map((selector) => {
          const node = document.querySelector(selector);
          if (!node) return [selector, null];
          const rect = node.getBoundingClientRect();
          return [selector, { left: rect.left, right: rect.right, width: rect.width }];
        }),
      );
      return {
        viewport: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        bodyScrollWidth: document.body.scrollWidth,
        boxes,
      };
    });
    const overflow = result.scrollWidth > result.viewport;
    failed ||= overflow;
    console.log(JSON.stringify({ file, overflow, ...result }));
    await page.close();
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
