// 刷题页另需的几个图标,画法与 wb/icons.js 相同(24×24,描边用 currentColor)。
// 白板的图标集里没有它们,加在同一张表上,用法不变:icon(name)。

import { ICONS, icon } from "./wb/icons.js";

const path = (d) => `<path d="${d}"/>`;

Object.assign(ICONS, {
  forward: path("M9.5 5.5L16 12l-6.5 6.5"),
  list: path("M9 6.5h10.5M9 12h10.5M9 17.5h10.5") +
    `<circle cx="5" cy="6.5" r=".6"/><circle cx="5" cy="12" r=".6"/><circle cx="5" cy="17.5" r=".6"/>`,
  copy: `<rect x="8.5" y="8.5" width="11" height="11" rx="2"/>` +
    path("M15.5 8.5V6a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5"),
  history: path("M4.6 12a7.4 7.4 0 1 0 2.2-5.3") + path("M4.2 4.7v4.3h4.3") + path("M12 8.2v4.2l2.8 1.8"),
  bulb: path("M9.4 17.6h5.2") + path("M10.3 20.6h3.4") +
    path("M12 3.4a5.8 5.8 0 0 0-3.5 10.4c.6.5 1 1.2 1 2v.3h5v-.3c0-.8.4-1.5 1-2A5.8 5.8 0 0 0 12 3.4z"),
  alert: path("M10.3 4.9L3.4 17.2a2 2 0 0 0 1.7 2.9h13.8a2 2 0 0 0 1.7-2.9L13.7 4.9a2 2 0 0 0-3.4 0z") +
    path("M12 9.6v4.2") + path("M12 16.9h.01"),
  wall: `<rect x="3.5" y="4.5" width="5" height="4" rx="1"/><rect x="10" y="4.5" width="10.5" height="4" rx="1"/>` +
    `<rect x="3.5" y="10" width="8" height="4" rx="1"/><rect x="13" y="10" width="7.5" height="4" rx="1"/>` +
    `<rect x="3.5" y="15.5" width="11" height="4" rx="1"/><rect x="16" y="15.5" width="4.5" height="4" rx="1"/>`,
  ledger: path("M6 3.8h12a1.5 1.5 0 0 1 1.5 1.5v13.4a1.5 1.5 0 0 1-1.5 1.5H6a1.5 1.5 0 0 1-1.5-1.5V5.3A1.5 1.5 0 0 1 6 3.8z") +
    path("M8.2 8.6l1.6 1.6 2.6-3") + path("M14.4 8.8h2.6") + path("M8.4 14.2l3.2 3.2M11.6 14.2l-3.2 3.2") + path("M14.4 15.8h2.6"),
  rail: `<rect x="3.5" y="4.5" width="17" height="15" rx="2"/>` + path("M9 4.5v15"),
  panel: `<rect x="3.5" y="4.5" width="17" height="15" rx="2"/>` + path("M15 4.5v15"),
  tick: path("M3.2 12.6c1.6 1.3 3.1 3 4.4 5.2C10.4 12 14.4 7.2 20.8 3.6"),
  timer: `<circle cx="12" cy="13.2" r="7.2"/>` + path("M12 9.6v3.8l2.4 1.6") + path("M9.6 3.6h4.8"),
  play: path("M8 5.5v13l10.5-6.5z"),
  lock: `<rect x="5.5" y="10.5" width="13" height="9.5" rx="2"/>` + path("M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"),
});

export { icon };
