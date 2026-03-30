# 控制台前端静态资源

| 文件 | 说明 |
|------|------|
| `index.html` | 页面骨架（模板 + 挂载点 `#app`） |
| `css/dashboard.css` | 控制台专用样式 |
| `js/dashboard-app.js` | Vue 3 应用（选项式 API，无打包步骤） |
| `vendor/` | 本地托管的 Vue / Bootstrap JS（避免外网 CDN 失败） |
| `sample_screenplay.json` | 剧本 JSON 示例 |

后续若逻辑继续膨胀，可在 **不加构建工具** 的前提下把 `dashboard-app.js` 再拆成多个 `<script src>` 按模块加载；若需要组件化与类型检查，再引入 Vite + Vue SFC 等工具链。
