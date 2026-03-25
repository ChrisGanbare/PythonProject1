# 设置 UI 功能恢复计划

**日期**: 2026-03-25  
**优先级**: 🔴 P0 (关键功能缺失)

---

## 🐛 问题确认

### 问题 1: AI 配置 UI 入口缺失 🔴

**现状**:
- ✅ `index_old.html` 有完整的全局设置模态框 (1400+ 行)
- ❌ `index.html` (新首页) 无设置入口
- ❌ `code_studio.html` 无设置入口
- ❌ AI 编译页面无设置入口

**影响**:
- 用户无法配置 OpenAI API
- AI 编译功能无法使用
- 用户体验断裂

**修复方案**:
1. 在首页添加"设置"按钮 (右上角)
2. 创建独立设置模态框
3. 或在 AI 编译页面添加"AI 配置"入口

---

### 问题 2: 渲染质量预设无 UI 🔴

**现状**:
- ✅ `shared/config/settings.py` 有质量预设代码
- ❌ 无 UI 供用户选择

**影响**:
- 用户无法调整渲染质量
- 无法平衡速度和质量

**修复方案**:
1. 在首页 4 步向导中添加"高级选项"
2. 或在项目管理页面添加"全局设置"

---

### 问题 3: 环境变量管理需升级 🟡

**现状**:
- ✅ 使用 `.env` 文件
- ❌ 不支持服务器部署
- ❌ 无数据库支持

**修复方案**:
1. 短期：保持 `.env`，添加 UI 管理界面
2. 中期：引入 SQLite (轻量级)
3. 长期：支持多种配置后端

---

## 📋 实施计划

### 阶段 1: 恢复 AI 配置 UI (立即)

**目标**: 让用户可以配置 OpenAI API

**步骤**:
1. 从 `index_old.html` 提取设置模态框代码
2. 创建独立组件 `settings-modal.html`
3. 在以下页面添加入口:
   - 首页 (右上角齿轮图标)
   - AI 编译页面 (配置提示)
   - 代码工坊页面 (设置菜单)

**验收标准**:
- [ ] 用户可以打开设置模态框
- [ ] 可以填写 Base URL、API Key
- [ ] 可以验证 API 连接
- [ ] 配置保存到 `.env` 或数据库

---

### 阶段 2: 添加渲染质量 UI (短期)

**目标**: 用户可以调整渲染质量

**步骤**:
1. 在首页 4 步向导的步骤 4 添加"高级选项"
2. 添加质量选择下拉框:
   - Preview (快速预览)
   - Draft (草稿质量)
   - Final (最终质量)
3. 显示各质量的参数详情 (DPI、比特率等)

**验收标准**:
- [ ] 用户可以选择质量预设
- [ ] 显示当前质量的参数
- [ ] 选择后影响渲染结果

---

### 阶段 3: 升级配置管理 (中期)

**目标**: 支持服务器部署

**步骤**:
1. 引入 SQLite 存储配置
2. 保持 `.env` 向后兼容
3. 添加配置管理 API:
   - `GET /api/settings` - 获取配置
   - `POST /api/settings` - 更新配置
   - `GET /api/settings/validate` - 验证配置

**验收标准**:
- [ ] 支持本地 `.env` 模式
- [ ] 支持 SQLite 数据库模式
- [ ] 支持环境变量覆盖
- [ ] 服务器部署友好

---

## 🎯 设计方案

### 方案 A: 独立设置页面 (推荐)

**优点**:
- 清晰的导航结构
- 易于扩展
- 符合用户习惯

**入口**:
- 首页右上角齿轮图标
- 导航栏"设置"菜单项

**页面结构**:
```
设置
├── AI 配置
│   ├── Base URL
│   ├── API Key
│   ├── 模型选择
│   └── 验证连接
├── 渲染设置
│   ├── 质量预设
│   ├── 分辨率
│   └── FPS
├── 品牌主题
│   └── 自定义颜色
└── 系统设置
    ├── 日志级别
    └── 存储路径
```

---

### 方案 B: 情境化设置 (备选)

**优点**:
- 减少页面跳转
- 情境相关

**入口**:
- AI 编译页面：检测未配置时弹出
- 首页：步骤 4 高级选项

**缺点**:
- 配置分散，不易管理
- 难以发现所有配置项

---

## 📝 代码实现

### 1. 设置模态框组件

```html
<!-- 模态框 -->
<div class="modal fade" id="settingsModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">
          <i class="bi bi-gear-fill me-2"></i>全局设置
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <!-- AI 配置 -->
        <h6 class="fw-bold mb-3">
          <i class="bi bi-cpu-fill me-2 text-primary"></i>AI 配置
        </h6>
        <div class="mb-3">
          <label class="form-label">Base URL *</label>
          <input type="text" class="form-control" v-model="settings.openai_base_url" 
                 placeholder="https://api.openai.com/v1">
        </div>
        <div class="mb-3">
          <label class="form-label">API Key *</label>
          <input type="password" class="form-control" v-model="settings.openai_api_key" 
                 placeholder="sk-...">
        </div>
        <div class="mb-3">
          <label class="form-label">模型</label>
          <select class="form-select" v-model="settings.openai_model">
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="gpt-4">GPT-4</option>
            <option value="qwen-turbo">通义千问 Turbo</option>
          </select>
        </div>
        <button class="btn btn-outline-primary btn-sm" @click="validateAPI">
          <i class="bi bi-check-circle me-1"></i>验证连接
        </button>
        
        <!-- 渲染质量 -->
        <h6 class="fw-bold mb-3 mt-4">
          <i class="bi bi-film me-2 text-primary"></i>渲染质量
        </h6>
        <div class="mb-3">
          <label class="form-label">质量预设</label>
          <select class="form-select" v-model="settings.quality_preset">
            <option value="preview">Preview - 快速预览 (72 DPI)</option>
            <option value="draft">Draft - 草稿质量 (108 DPI)</option>
            <option value="final">Final - 最终质量 (144 DPI)</option>
          </select>
          <div class="form-text">
            <strong>当前参数:</strong> 
            DPI: {{ qualityParams.dpi }}, 
            比特率：{{ qualityParams.bitrate }}kbps,
            CRF: {{ qualityParams.crf }}
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
        <button type="button" class="btn btn-primary" @click="saveSettings">
          <i class="bi bi-save me-1"></i>保存设置
        </button>
      </div>
    </div>
  </div>
</div>
```

### 2. 首页入口

```html
<!-- 右上角设置按钮 -->
<div class="position-absolute top-0 end-0 p-4">
  <button class="btn btn-outline-light btn-lg" data-bs-toggle="modal" data-bs-target="#settingsModal">
    <i class="bi bi-gear-fill"></i>
  </button>
</div>
```

### 3. API 接口

```python
# api/settings.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shared.config.settings import settings

router = APIRouter()

class SettingsUpdate(BaseModel):
    openai_base_url: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    quality_preset: str | None = None

@router.get("/api/settings")
async def get_settings():
    """获取当前配置"""
    return settings.to_dict()

@router.post("/api/settings")
async def update_settings(new_settings: SettingsUpdate):
    """更新配置"""
    # TODO: 实现配置保存
    return {"status": "success"}

@router.post("/api/settings/validate")
async def validate_settings():
    """验证 API 配置"""
    # TODO: 实现 API 验证
    return {"valid": True}
```

---

## ✅ 验收标准

### AI 配置
- [ ] 设置按钮可见可点击
- [ ] 模态框正常打开
- [ ] 可以填写 Base URL、API Key、模型
- [ ] 可以验证 API 连接
- [ ] 配置保存成功
- [ ] AI 编译功能可以使用

### 渲染质量
- [ ] 质量预设下拉框显示
- [ ] 选择后显示参数详情
- [ ] 影响实际渲染输出

### 配置管理
- [ ] 支持 `.env` 文件保存
- [ ] 配置持久化
- [ ] 重启后配置保留

---

## 📊 优先级

| 任务 | 优先级 | 预计工时 |
|------|--------|----------|
| 恢复 AI 配置 UI | 🔴 P0 | 4 小时 |
| 添加渲染质量 UI | 🔴 P0 | 2 小时 |
| 配置管理 API | 🟡 P1 | 4 小时 |
| SQLite 支持 | 🟢 P2 | 8 小时 |

---

**下一步**: 立即实施方案 A - 独立设置页面
