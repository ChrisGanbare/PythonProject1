# API Key 明文/密文切换功能

**更新日期**: 2026-03-25  
**版本**: v2.3.2

---

## 🎯 功能说明

在全局设置模态框的 API Key 输入框右侧添加了**眼睛图标按钮**，点击可在明文和密文之间切换显示。

---

## ✨ UI 交互

### 默认状态 (密文)
```
┌─────────────────────────────────────────────┐
│ API Key *                              [👁] │
│ sk-••••••••••••••••••••••••abcd1234         │
└─────────────────────────────────────────────┘
```

### 点击后 (明文)
```
┌─────────────────────────────────────────────┐
│ API Key *                              [👁‍🗨] │
│ sk-6e81bb8d9fa44d1da4da71f4202bcf9d         │
└─────────────────────────────────────────────┘
```

---

## 🔧 技术实现

### HTML 结构

```html
<div class="input-group">
  <input type="password" 
         class="form-control font-monospace" 
         id="settingsApiKey"
         placeholder="sk-..."
         autocomplete="off"
         style="letter-spacing: 2px;">
  <button class="btn btn-outline-secondary" 
          type="button" 
          id="btnToggleApiKey"
          onclick="toggleApiKeyVisibility()"
          title="显示/隐藏 API Key">
    <i class="bi bi-eye" id="iconToggleApiKey"></i>
  </button>
</div>
```

### JavaScript 函数

```javascript
// 切换 API Key 显示/隐藏
function toggleApiKeyVisibility() {
  const apiKeyInput = document.getElementById('settingsApiKey');
  const toggleIcon = document.getElementById('iconToggleApiKey');
  const toggleBtn = document.getElementById('btnToggleApiKey');
  
  if (apiKeyInput.type === 'password') {
    // 切换到明文显示
    apiKeyInput.type = 'text';
    toggleIcon.className = 'bi bi-eye-slash';
    toggleBtn.title = '隐藏 API Key';
    toggleBtn.classList.add('btn-warning');
    toggleBtn.classList.remove('btn-outline-secondary');
  } else {
    // 切换到密文显示
    apiKeyInput.type = 'password';
    toggleIcon.className = 'bi bi-eye';
    toggleBtn.title = '显示 API Key';
    toggleBtn.classList.remove('btn-warning');
    toggleBtn.classList.add('btn-outline-secondary');
  }
  
  // 聚焦到输入框
  apiKeyInput.focus();
}
```

---

## 🎨 视觉反馈

### 按钮状态

| 状态 | 图标 | 按钮样式 | 提示文本 |
|------|------|----------|----------|
| 密文 (默认) | 👁️ `bi-eye` | `btn-outline-secondary` | 显示 API Key |
| 明文 | 👁️‍🗨️ `bi-eye-slash` | `btn-warning` | 隐藏 API Key |

### 动画效果

- 点击按钮时，输入框类型立即切换
- 按钮颜色变化 (灰色 → 黄色)
- 图标变化 (眼睛 → 眼睛加斜线)
- 自动聚焦到输入框

---

## 📊 API Key 状态显示

### 已保存状态

```
┌──────────────────────────────────────────────────────┐
│ API Key *                                        [👁] │
│ sk-••••••••••••••••••••••••abcd1234                  │
│                                                      │
│ 🛡️ 请妥善保管您的 API Key，仅存储在本地浏览器。       │
│    ✅ 已保存：sk••••1234                              │
└──────────────────────────────────────────────────────┘
```

### 未保存状态

```
┌──────────────────────────────────────────────────────┐
│ API Key *                                        [👁] │
│                                                       │
│ 🛡️ 请妥善保管您的 API Key，仅存储在本地浏览器。       │
│    ⚠️ 未保存                                          │
└──────────────────────────────────────────────────────┘
```

---

## 🔒 安全特性

### 1. 本地存储
- API Key 仅存储在浏览器 localStorage
- 不会上传到服务器
- 仅在当前浏览器可用

### 2. 默认密文
- 输入框默认为 `type="password"`
- 防止旁人偷看
- 需要主动点击才能显示明文

### 3. 自动聚焦
- 切换后自动聚焦到输入框
- 方便继续编辑
- 减少鼠标移动

### 4. 掩码显示
- 保存状态显示掩码：`sk••••1234`
- 只显示首尾 4 个字符
- 保护敏感信息

---

## ✅ 使用场景

### 场景 1: 首次配置 API Key

1. 打开全局设置
2. 看到 API Key 输入框 (密文模式)
3. 输入 API Key (显示为圆点)
4. 点击眼睛图标查看明文
5. 确认输入正确
6. 点击"验证连接"
7. 保存设置

---

### 场景 2: 修改已保存的 API Key

1. 打开全局设置
2. 看到"✅ 已保存：sk••••1234"
3. 输入框显示已保存的 API Key (密文)
4. 点击眼睛图标查看完整明文
5. 修改 API Key
6. 再次点击眼睛图标确认
7. 保存设置

---

### 场景 3: 检查 API Key 是否正确

1. 打开全局设置
2. 点击眼睛图标切换到明文
3. 检查 API Key 是否正确
4. 如果错误，直接修改
5. 点击"验证连接"测试
6. 保存设置

---

## 🧪 测试验证

### 功能测试

| 测试项 | 预期结果 | 实际结果 | 状态 |
|--------|----------|----------|------|
| 默认密文显示 | type=password | ✅ | 通过 |
| 点击切换明文 | type=text | ✅ | 通过 |
| 再次点击切回密文 | type=password | ✅ | 通过 |
| 图标变化 | eye ↔ eye-slash | ✅ | 通过 |
| 按钮样式变化 | gray ↔ yellow | ✅ | 通过 |
| 自动聚焦 | 输入框获得焦点 | ✅ | 通过 |
| API Key 状态显示 | 已保存/未保存 | ✅ | 通过 |

**测试通过率**: 7/7 (100%) ✅

---

## 📝 代码位置

| 文件 | 函数/组件 | 说明 |
|------|----------|------|
| `static/settings-modal.html` | `toggleApiKeyVisibility()` | 切换函数 |
| `static/settings-modal.html` | `checkApiKeyStatus()` | 状态检查 |
| `static/settings-modal.html` | API Key input group | HTML 结构 |
| `static/settings-modal.html` | `loadSettings()` | 加载时调用 |
| `static/settings-modal.html` | `saveSettings()` | 保存后更新 |

---

## 🎯 用户体验改进

### 改进前
- ❌ API Key 只能密文输入
- ❌ 无法确认输入是否正确
- ❌ 不知道是否已保存
- ❌ 修改时需要重新输入

### 改进后
- ✅ 一键切换明文/密文
- ✅ 可以查看完整 API Key
- ✅ 显示保存状态
- ✅ 方便检查和修改

---

## ⚠️ 注意事项

### 1. 公共场合使用
- 在公共场合使用明文模式时注意周围环境
- 使用后立即切换回密文模式
- 避免旁人偷看

### 2. 屏幕共享
- 屏幕共享时建议使用密文模式
- 如需演示，先打码 API Key
- 使用后立即切换回密文

### 3. 浏览器安全
- localStorage 仅在当前浏览器可用
- 清除浏览器数据会删除 API Key
- 建议备份 API Key

---

## 🔮 未来优化

### P1 (短期)
- [ ] 添加键盘快捷键 (Ctrl+Shift+E 切换)
- [ ] 添加复制按钮 (一键复制 API Key)
- [ ] 添加粘贴按钮 (从剪贴板粘贴)

### P2 (中期)
- [ ] 添加 API Key 强度检测
- [ ] 添加 API Key 过期提醒
- [ ] 添加多个 API Key 管理

### P3 (长期)
- [ ] 支持加密存储 (使用主密码)
- [ ] 支持 API Key 同步 (跨设备)
- [ ] 支持 API Key 轮换提醒

---

**文档版本**: 1.0  
**最后更新**: 2026-03-25  
**维护者**: PythonProject1 Team
