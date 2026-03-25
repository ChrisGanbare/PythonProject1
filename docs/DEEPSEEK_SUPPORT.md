# DeepSeek 模型支持与 API Key 交互优化

**更新日期**: 2026-03-25  
**版本**: v2.3.2

---

## 🎯 新增功能

### 1. DeepSeek 模型支持 ✅

**支持的模型**:
| 模型 | 说明 | 适用场景 |
|------|------|----------|
| `deepseek-chat` | DeepSeek Chat | 对话、文本生成 |
| `deepseek-coder` | DeepSeek Coder | 代码生成、代码补全 |
| `deepseek-v2` | DeepSeek V2 (最新版) | 通用任务 |

**Base URL**: `https://api.deepseek.com/v1`

---

### 2. 模型提供商选择器 ✅

**支持的提供商**:
| 提供商 | Base URL | 推荐模型 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo`, `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-coder` |
| 通义千问 (阿里云) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo`, `qwen-coder-plus` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k`, `moonshot-v1-32k` |
| 自定义 / 其他 | 手动输入 | 手动输入模型名称 |

---

### 3. API Key 与模型不匹配处理 ✅

**问题场景**:
- 用户使用阿里云 API Key，但选择了 OpenAI 模型
- 用户使用 DeepSeek API Key，但选择了通义千问模型
- 用户使用阿里云 `coding plan`，但模型列表中没有对应模型

**解决方案**:

#### 3.1 验证时检测模型可用性

```javascript
// 验证 API 连接时获取可用模型列表
const modelsResponse = await fetch(`${baseUrl}/models`, {
  headers: { 'Authorization': `Bearer ${apiKey}` }
});

// 检查当前选中的模型是否在可用列表中
const modelExists = availableModels.some(m => m.id === currentModel);

if (!modelExists) {
  // 显示不匹配提示
  showModelMismatchAlert();
}
```

#### 3.2 友好的错误提示

**401 Unauthorized**:
```
❌ API Key 无效

请检查：
1. API Key 是否正确
2. Base URL 是否正确
3. API Key 是否有余额
```

**403 Forbidden**:
```
❌ API Key 无权限

可能原因：
1. API Key 不支持当前 API 端点
2. 需要开通相关服务

建议：
- 阿里云用户请确保开通了百炼平台服务
- DeepSeek 用户请确保开通了 API 服务
```

**模型不匹配**:
```
⚠️ API 连接成功，但当前模型 "xxx" 不可用。

可用模型：qwen-turbo, qwen-plus, qwen-max 等共 10 个模型

请切换提供商或手动输入模型名称。

[切换到通义千问] [切换到 DeepSeek]
```

---

## 🔧 使用指南

### 场景 1: 使用 DeepSeek

**步骤**:
1. 打开全局设置 (点击右上角齿轮图标)
2. 选择"模型提供商" → **DeepSeek (深度求索)**
3. 填写 Base URL: `https://api.deepseek.com/v1` (自动填充)
4. 填写 API Key: `sk-xxx` (DeepSeek API Key)
5. 选择模型：**deepseek-chat** 或 **deepseek-coder**
6. 点击"验证连接"
7. 保存设置

---

### 场景 2: 使用阿里云百炼平台 (coding plan)

**步骤**:
1. 打开全局设置
2. 选择"模型提供商" → **通义千问 (阿里云)**
3. 填写 Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1` (自动填充)
4. 填写 API Key: `sk-xxx` (阿里云 API Key)
5. 选择模型：
   - 如果有 `qwen-coder-plus` → 选择此项
   - 如果没有 → 选择"自定义 / 其他"，手动输入模型名称
6. 点击"验证连接"
7. 如果提示模型不匹配，点击"切换到通义千问"按钮
8. 保存设置

---

### 场景 3: 使用自定义模型

**步骤**:
1. 打开全局设置
2. 选择"模型提供商" → **自定义 / 其他**
3. 填写 Base URL: 自定义 API 地址
4. 填写 API Key: 自定义 API Key
5. 在"模型"下拉框中选择"自定义"，下方会出现输入框
6. 手动输入模型名称，例如：`deepseek-coder` 或 `qwen-coder-plus`
7. 点击"验证连接"
8. 保存设置

---

## 📊 模型对比

### OpenAI 系列
| 模型 | 速度 | 质量 | 价格 | 推荐场景 |
|------|------|------|------|----------|
| GPT-3.5 Turbo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | $ | 快速测试、简单任务 |
| GPT-4o Mini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ | 日常使用、性价比高 |
| GPT-4o | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $$$$ | 高质量输出、复杂任务 |

### DeepSeek 系列
| 模型 | 速度 | 质量 | 价格 | 推荐场景 |
|------|------|------|------|----------|
| deepseek-chat | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ | 对话、文本生成 |
| deepseek-coder | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $$ | 代码生成、代码补全 |
| deepseek-v2 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $$$ | 最新模型、通用任务 |

### 通义千问系列
| 模型 | 速度 | 质量 | 价格 | 推荐场景 |
|------|------|------|------|----------|
| qwen-turbo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ¥ | 快速测试 |
| qwen-plus | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ¥¥ | 日常使用 |
| qwen-max | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ¥¥¥ | 高质量输出 |
| qwen-coder-plus | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ¥¥ | 代码生成 |

---

## ⚠️ 常见问题

### Q1: 阿里云用户提示"模型不可用"怎么办？

**A**: 这说明您的 API Key 不支持当前选中的模型。

**解决方案**:
1. 点击"切换到通义千问"按钮
2. 在模型列表中选择可用的模型 (如 `qwen-turbo`)
3. 或者选择"自定义 / 其他"，手动输入模型名称

---

### Q2: 如何知道我的 API Key 支持哪些模型？

**A**: 点击"验证连接"按钮，系统会自动获取可用模型列表。

如果 API Key 有效但模型不匹配，会显示：
```
✅ API 连接成功！

可用模型数量：10
当前模型 "xxx" 不可用。

可用模型：qwen-turbo, qwen-plus, qwen-max...
```

---

### Q3: DeepSeek API 的 Base URL 是什么？

**A**: `https://api.deepseek.com/v1`

在设置中选择"DeepSeek (深度求索)"提供商后，Base URL 会自动填充。

---

### Q4: 自定义模型如何使用？

**A**: 
1. 选择"模型提供商" → **自定义 / 其他**
2. 填写自定义 Base URL
3. 填写 API Key
4. 在模型下拉框中选择"自定义"
5. 在下方输入框中手动输入模型名称
6. 点击"验证连接"

---

## 📝 代码实现

### 提供商与 Base URL 映射

```javascript
const PROVIDER_BASE_URLS = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com/v1',
  dashscope: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  moonshot: 'https://api.moonshot.cn/v1'
};
```

### 模型列表动态更新

```javascript
function updateModelOptions() {
  const provider = document.getElementById('settingsProvider').value;
  
  // 隐藏所有 optgroup
  document.querySelectorAll('#settingsModel optgroup').forEach(og => {
    og.style.display = 'none';
  });
  
  // 显示选中的提供商对应的 optgroup
  const selectedOptgroup = document.getElementById(`optgroup-${provider}`);
  if (selectedOptgroup) {
    selectedOptgroup.style.display = 'block';
  }
  
  // 自定义模式显示输入框
  if (provider === 'custom') {
    document.getElementById('settingsCustomModel').style.display = 'block';
  }
}
```

### API Key 验证与模型检测

```javascript
async function validateAPI() {
  // 获取可用模型列表
  const modelsResponse = await fetch(`${baseUrl}/models`, {
    headers: { 'Authorization': `Bearer ${apiKey}` }
  });
  
  const modelsData = await modelsResponse.json();
  const availableModels = modelsData.data || [];
  
  // 检查当前模型是否可用
  const modelExists = availableModels.some(m => m.id === currentModel);
  
  if (!modelExists) {
    // 显示不匹配提示
    document.getElementById('modelMismatchAlert').style.display = 'block';
  }
}
```

---

## ✅ 验收标准

### P0 (关键功能)
- [x] DeepSeek 模型支持
- [x] 模型提供商选择器
- [x] 自定义模型输入
- [x] API Key 验证
- [x] 模型不匹配检测
- [x] 友好的错误提示

### P1 (重要功能)
- [x] 快速切换提供商按钮
- [x] 可用模型列表显示
- [x] Base URL 自动填充
- [x] 配置持久化 (localStorage)

### P2 (优化功能)
- [ ] 模型列表缓存
- [ ] 模型使用统计
- [ ] 推荐模型智能提示

---

**文档版本**: 1.0  
**最后更新**: 2026-03-25  
**维护者**: PythonProject1 Team
