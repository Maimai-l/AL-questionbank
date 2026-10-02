# wb/

刷题页的工具栏、图标和界面样式取自 white-board(`Maimai-l/white-board`,提交
`373432a`,Version 1.1.0),与白板应用保持同一套外观和手感。

| 文件 | 来源 | 改动 |
|---|---|---|
| `icons.js` | `whiteboard/web/static/js/icons.js` | 无 |
| `pkpicker.js` | `whiteboard/web/static/js/pkpicker.js` | 两处导入路径:`/inksync/util.js` → `./util.js`,`../vendor/` → `./vendor/` |
| `vendor/pencilkit-picker.js` | `whiteboard/web/static/vendor/pencilkit-picker.js` | 无(第三方文件,见 `vendor/README.md`) |
| `util.js` | `packages/inksync/inksync/web/util.js` 中的 `clamp` 与 `el` | 无 |
| `wb.css` | `whiteboard/web/static/css/app.css` 的摘录 | 无,摘录的行号写在文件开头 |

工具栏的行为(每件工具各记颜色与粗细、颜色与粗细弹层、橡皮的两种模式、iPad 上
换成笔具盘)由 `../tools.js` 按 white-board 的 `ui.js` 移植。

white-board 更新后,按上表重新复制这些文件即可;`pkpicker.js` 的两处路径要再改一次。
