// 가이드 페이지 자동 점검
//   node _tools/qa.mjs preview/index.html
//   node _tools/qa.mjs index.html
//
// 모든 단계(.step)를 여러 화면 폭에서 열어 보고
//   · 가로 스크롤(레이아웃 넘침) · 스크립트 오류 · 복사 버튼이 빈 내용을 복사하는지
// 를 확인한다. 문제가 있으면 종료 코드 1.
import path from 'path';

const target = process.argv[2] || 'preview/index.html';
const url = 'file://' + path.resolve(target);

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import('/opt/node22/lib/node_modules/playwright/index.mjs')); }

const WIDTHS = [1280, 960, 760, 640, 390];
const browser = await chromium.launch();
const problems = [];

for (const w of WIDTHS) {
  const ctx = await browser.newContext({ viewport: { width: w, height: 900 },
                                         permissions: ['clipboard-read', 'clipboard-write'] });
  const page = await ctx.newPage();
  page.on('pageerror', e => problems.push(`${w}px 스크립트 오류: ${e.message}`));
  await page.goto(url);
  await page.waitForTimeout(300);

  const steps = await page.$$eval('.step', els => els.map(e => e.id));
  const over = [];
  for (const id of steps) {
    await page.evaluate(x => window.go && window.go(x), id);
    await page.waitForTimeout(120);
    const o = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    if (o) over.push(id);
  }
  if (over.length) problems.push(`${w}px 가로 넘침: ${over.join(', ')}`);

  if (w === WIDTHS[0]) {
    console.log(`단계 ${steps.length}개: ${steps.join(' ')}`);
    // 복사 버튼: 대상이 있고 내용이 비어 있지 않은지
    const ids = await page.$$eval('[data-copy]', els => [...new Set(els.map(e => e.dataset.copy))]);
    const empty = await page.evaluate(list => list.filter(id => {
      const el = document.getElementById(id);
      return !el || !(el.textContent || '').trim();
    }), ids);
    console.log(`복사 대상 ${ids.length}종`);
    if (empty.length) problems.push(`복사 대상이 없거나 비어 있음: ${empty.join(', ')}`);
  }
  await ctx.close();
}
await browser.close();

console.log(`점검 폭: ${WIDTHS.join(' / ')}px`);
if (problems.length) {
  console.log('\n문제 발견:');
  problems.forEach(p => console.log('  ✗ ' + p));
  process.exit(1);
}
console.log('✓ 이상 없음');
