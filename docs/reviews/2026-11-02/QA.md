# Documentation QA evidence

## Implemented and statically checked

- Canonical sources, generated page URLs, original anchors, active navigation, single primary heading, unique IDs, Markdown/HTML links/assets, SVG XML, version/license metadata and deterministic generation are covered by `tests/test_documentation.py`.
- Native details/summary navigation is preserved. JavaScript keeps the menu open on resize when it contains focus. Reading and links do not depend on JS.
- Code remains locally scrollable and unwrapped for exact copying. Blocks are keyboard-focusable, focus outlines are visible in CSS, and font sizes are 13px desktop / 12px mobile. Copy uses native buttons, exact `code.textContent`, and success feedback only after clipboard resolution; failure offers manual selection. Status is announced through a polite live region.
- SVGs have alt text and full-size links; reduced-motion styling remains. No new logo or fake screenshot is introduced.
- `contrast.json` records calculated solid-color sRGB ratios: body 15.77, muted 8.88, link/focus 9.89, primary button 9.27, code 12.67, sidebar labels 5.37. These do not cover every state/gradient/image or establish full WCAG compliance.

## Rendered acceptance remains blocked

| Viewport | Screenshot | DOM/global overflow | Keyboard/menu | Clipboard/code scroll | Status |
| --- | --- | --- | --- | --- | --- |
| 320 | Not produced | Not measured | Not exercised | Not exercised | BLOCKED |
| 390 | Attempted earlier; browser exited | Not measured | Not exercised | Not exercised | BLOCKED |
| 768 | Not produced | Not measured | Not exercised | Not exercised | BLOCKED |
| 1440 | Not produced | Not measured | Not exercised | Not exercised | BLOCKED |

No browser-layout pass is inferred from CSS alone. No screen-reader, no-JS browser, browser-console/image-loading or production-like HTTP base-path result is claimed. Relative URLs are statically checked against the `/BuildRelay/` structure.

## Exact browser failures from this implementation session, before reset

The owner requested headless instead of native Firefox. These attempts were made earlier in this same task; they were not repeated during reapplication:

- Browser inventory: `Browsers: Error: The browser access host is unavailable`.
- Native fallback: `Computer Use was not approved to use Firefox`; discontinued.
- Local module check: `python playwright: False`; Node could not resolve playwright, @playwright/test or puppeteer.
- Runtime imports: `The requested module './index.js' does not provide an export named 'default'` (also surfaced with `SyntaxError:` prefix).
- CommonJS fallback: `Cannot find module 'playwright'`, require stack rooted at this project's package.json.
- Installed browser reported `Mozilla Firefox 158.0.1`.
- Headless command below printed `*** You are running in headless mode.` and exited **134**. Cause not established; no screenshot was produced.

```bash
/Applications/Firefox.app/Contents/MacOS/firefox --headless --no-remote --profile '/Users/ehsan/Projects/AP-V2/LinkedIn post/docs-headless-profile' --window-size 390,844 --screenshot /Users/ehsan/Projects/AP-V2/docs/reviews/2026-11-02/screenshots/introduction-390.png file:///Users/ehsan/Projects/AP-V2/docs/index.html
```

No browser/package download or unsandboxed retry was performed. The screenshot path above is an attempted output, not evidence of a file.

## Next rendered QA

In an approved functioning headless environment, serve docs at `/BuildRelay/`; capture all four viewports and assert no global horizontal overflow, while testing code scrolling separately. Exercise keyboard menu open/close, destinations, focus retention on resize, actual clipboard contents, clipboard denial feedback, no-JS reading/navigation, SVG loading/enlargement and browser console errors. Record browser version and viewport with each screenshot. Assistive-technology coverage remains separate.
