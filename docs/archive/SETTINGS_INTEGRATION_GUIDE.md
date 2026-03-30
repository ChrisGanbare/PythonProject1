# 全局设置模态框集成指南

**日期**: 2026-03-25  
**状态**: ✅ 组件已创建，待集成

---

## 📦 已创建的文件

| 文件 | 说明 | 状态 |
|------|------|------|
| `static/settings-modal.html` | 全局设置模态框组件 | ✅ 已完成 |
| `docs/SETTINGS_UI_RESTORE_PLAN.md` | 恢复计划文档 | ✅ 已完成 |
| `docs/GLOBAL_SETTINGS_MIGRATION.md` | 重构对比报告 | ✅ 已完成 |

---

## 🔧 集成步骤

### 步骤 1: 在 index.html 中引入设置模态框

在 `D:\PythonProject1\static\index.html` 的 `</body>` 标签前添加：

```html
<!-- 引入全局设置模态框 -->
<script src="settings-modal.html"></script>
```

### 步骤 2: 在首页添加设置按钮

在首页 Header 区域添加设置按钮（右上角）：

```html
<!-- 在 .header div 内添加 -->
<div class="position-absolute top-0 end-0 p-3">
    <button class="btn btn-outline-light btn-lg" 
            data-bs-toggle="modal" 
            data-bs-target="#settingsModal"
            title="全局设置">
        <i class="bi bi-gear-fill"></i>
    </button>
</div>
```

### 步骤 3: 在 Vue 应用中注册组件

在 `index.html` 的 Vue 应用中添加：

```javascript
const { createApp } = Vue

createApp({
    data() {
        return {
            // ... existing data
        }
    },
    mounted() {
        // Listen for settings updates
        window.addEventListener('settings-updated', (event) => {
            console.log('Settings updated:', event.detail)
            // Update local settings if needed
        })
    }
}).mount('#app')
```

---

## 🎯 功能说明

### AI 配置

- **Base URL**: OpenAI 兼容 API 地址
- **API Key**: API 密钥
- **模型选择**: GPT-3.5/4, 通义千问，Moonshot 等
- **验证连接**: 测试 API 是否可用

### 渲染设置

- **质量预设**: Preview/Draft/Final
- **分辨率**: 宽度 x 高度
- **帧率**: 24/25/30/60 FPS

### 存储设置

- **输出目录**: 视频保存位置
- **配置存储**: localStorage (短期) → SQLite (中期)

---

## 📊 存储方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **localStorage** | 简单、无需后端 | 仅浏览器可用 | 本地开发 |
| **`.env` 文件** | 持久化、可版本控制 | 需重启生效 | 单机部署 |
| **SQLite** | 轻量、支持并发 | 需实现 API | 服务器部署 |
| **PostgreSQL** | 强大、支持分布式 | 重量级 | 大型部署 |

---

## 🔄 迁移路径

### 阶段 1: localStorage (当前)

```javascript
// 保存到浏览器
localStorage.setItem('openai_api_key', 'sk-...')

// 读取
const apiKey = localStorage.getItem('openai_api_key')
```

**优点**: 立即可用，无需后端  
**缺点**: 仅当前浏览器可用

---

### 阶段 2: SQLite (推荐中期方案)

**数据库表结构**:

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入配置
INSERT INTO settings (key, value) VALUES 
    ('openai_base_url', 'https://api.openai.com/v1'),
    ('openai_api_key', 'sk-...'),
    ('quality_preset', 'draft');
```

**API 接口**:

```python
# api/settings.py

@router.get("/api/settings")
async def get_settings():
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    return {row[0]: row[1] for row in cursor.fetchall()}

@router.post("/api/settings")
async def update_settings(settings: dict):
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    for key, value in settings.items():
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
    conn.commit()
    return {"status": "success"}
```

**优点**: 
- 支持多用户
- 配置持久化
- 服务器部署友好

**缺点**: 
- 需要实现后端 API
- 需要数据库迁移

---

### 阶段 3: 混合模式 (最佳实践)

```python
# 配置优先级：环境变量 > 数据库 > .env 文件 > 默认值

def get_setting(key, default=None):
    # 1. 环境变量 (最高优先级)
    if key in os.environ:
        return os.environ[key]
    
    # 2. 数据库
    db_value = db.get_setting(key)
    if db_value is not None:
        return db_value
    
    # 3. .env 文件
    env_value = load_dotenv(key)
    if env_value is not None:
        return env_value
    
    # 4. 默认值
    return default
```

---

## ✅ 验收标准

### UI 层面
- [ ] 设置按钮可见 (首页右上角)
- [ ] 点击可打开模态框
- [ ] 模态框样式美观
- [ ] 可以填写所有配置项

### 功能层面
- [ ] AI 配置可以验证连接
- [ ] 质量预设可以切换
- [ ] 配置可以保存
- [ ] 配置重启后保留

### 存储层面
- [ ] localStorage 可用
- [ ] 准备 SQLite 迁移方案
- [ ] 支持环境变量覆盖

---

## 📝 下一步行动

1. **立即**: 将 `settings-modal.html` 集成到 `index.html`
2. **短期**: 实现配置保存 API (`/api/settings`)
3. **中期**: 引入 SQLite 存储
4. **长期**: 支持多配置集切换

---

**文档版本**: 1.0  
**最后更新**: 2026-03-25  
**维护者**: PythonProject1 Team
