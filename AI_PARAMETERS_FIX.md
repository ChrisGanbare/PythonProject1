# AI 编译参数显示 & 验证修复

## 问题描述

用户在使用 AI 编译时遇到两个主要问题：

1. **参数显示问题**：
   - 消息提示："由于任务未定义参数，使用默认设置"
   - 用户在UI上看不到这些默认参数值是什么
   - 参数列表不完整，缺少任务定义中的参数

2. **运行失败问题**（"Extra inputs are not permitted"）：
   - AI生成的kwargs可能包含task manifest中没有定义的参数
   - Pydantic 验证失败导致 422 错误
   - 用户得不到清晰的错误提示

## 根本原因

### 后端：
1. **参数schema未暴露** - 编译响应中没有包含task的参数定义
2. **参数清理不彻底** - 没有在编译/验证阶段移除未声明的参数
3. **参数默认值未填充** - 缺失的参数没有用默认值补充

### 前端：
1. **参数显示逻辑简陋** - 只显示编译生成的kwargs，不显示完整的参数定义
2. **默认值不可见** - 用户无法知道默认参数值是什么
3. **参数不完整** - 当task定义了参数但AI没生成时，参数就不显示

## 解决方案

### 后端改进

#### 1. 在编译响应中添加任务参数定义
**文件**: `shared/agent/schemas.py` (L54-65)
```python
class AgentCompileResponse(BaseModel):
    # ... existing fields ...
    task_parameters: list[dict[str, Any]] | None = Field(
        default=None,
        description="Task 的参数定义（从 manifest 中提取），便于前端显示"
    )
```

#### 2. 编译时填充参数定义和默认值
**文件**: `shared/agent/compiler.py` (L131-151)
- 从manifest中提取任务的参数定义
- 将编译结果的kwargs与参数定义合并
- 填入缺失参数的默认值
- 移除未声明的参数（清理后端生成数据）

#### 3. 验证时清理未声明参数
**文件**: `shared/agent/validate.py` (L21, 58-93)
- 修改 `validate_standard_request()` 调用新的清理函数
- 新函数 `_clean_undeclared_kwargs()`：
  - 填入缺失参数的默认值
  - 移除不在manifest中的参数
  - 生成清理警告信息

### 前端改进

#### 显示完整的参数列表（包括默认值）
**文件**: `static/js/dashboard-app.js` (L1519-1548)

编译成功时的处理逻辑：
```javascript
// 合并 task_parameters 与 kwargs
this.agentEditedKwargs = {};
if (data.task_parameters && Array.isArray(data.task_parameters)) {
  // 1. 先加载所有参数的默认值
  data.task_parameters.forEach(param => {
    if (param.name && 'default' in param) {
      this.agentEditedKwargs[param.name] = param.default;
    }
  });
  // 2. 用编译的值覆盖默认值，实现"显示所有参数"
  if (data.standard_request.kwargs) {
    Object.assign(this.agentEditedKwargs, data.standard_request.kwargs);
  }
}
```

**效果**：
- UI显示所有task定义的参数
- 显示每个参数的默认值
- AI生成的值覆盖默认值
- 用户能看到完整的参数列表

## 数据流

```
编译结果 (后端)
├── success: true
├── standard_request: { project, task, kwargs }
├── task_parameters: [     ← NEW: 从manifest提取
│     { name: "loan_amount", type: "float", default: 2000000 },
│     { name: "annual_rate", type: "float", default: 0.042 },
│     ...
│   ]
└── warnings: [ ... ]("已清理未声明的参数..." )

↓ 前端处理

agentEditedKwargs (UI显示)
├── loan_amount: 2000000     (默认值)
├── annual_rate: 0.042        (默认值)
└── quality: "preview"        (AI生成的值，覆盖默认值)
```

## 修复效果

### ✅ 问题1：参数显示问题已解决
- **之前**：编译后参数区域根据kwargs显示，缺少默认值的参数
- **之后**：显示task manifest中定义的所有参数，包括默认值

### ✅ 问题2："Extra inputs" 错误已解决
- **之前**：AI生成未定义的参数 → Pydantic验证失败 → 422错误
- **之后**：编译和验证时自动清理未定义的参数 → 只有有效参数被传递 → 不再报验证错误

### ✅ 参数使用体验改善
- 用户编译后可以看到**完整的参数列表**
- 用户可以看到**每个参数的默认值**
- 用户可以在UI上**修改任何参数**
- 系统会**自动清理未声明的参数**，防止验证失败

## 测试场景

### 测试1：编译后参数显示
1. 输入提示："生成一个贷款对比视频"
2. 点击"编译"
3. **验证**：
   - 参数区应该显示 loan_amount, annual_rate, loan_years, quality, style 等
   - 每个参数都有默认值显示
   - 消息显示"任务参数：loan_amount, annual_rate, ..."

### 测试2：修改参数
1. 编译成功后
2. 在参数区修改 `loan_amount` 为 3000000
3. 点击"开始渲染"
4. **验证**：后端收到修改后的值，没有额外参数

### 测试3：验证与错误消息
1. 输入提示："生成视频，设置foobar参数为123"（foobar不存在）
2. 点击"编译"
3. **验证**：
   - 编译成功（AI可能生成foobar）
   - 日志显示警告："已清理未声明的参数：foobar"
   - 参数区不显示foobar
   - 点击"开始渲染"不会报"Extra inputs"错误

### 测试4：无参数任务
1. 选择一个没有参数定义的task（如smoke_check）
2. 编译后
3. **验证**：
   - 参数区空或显示（无参数定义）
   - 可正常运行

## 代码变更清单

| 文件 | 行号 | 变更说明 |
|------|------|---------|
| shared/agent/schemas.py | 54-65 | 添加 task_parameters 字段 |
| shared/agent/compiler.py | 131-151 | 填充task参数定义和默认值 |
| shared/agent/validate.py | 21, 58-93 | 新增`_clean_undeclared_kwargs` 函数 |
| static/js/dashboard-app.js | 1519-1548 | 合并参数定义与kwargs显示所有参数 |

## 配置变更

无额外配置需求。系统自动检测task manifest中的参数定义。

## 兼容性

- ✅ 现有能正常运行的任务不受影响
- ✅ 现有已保存的会话模板继续使用
- ✅ 无数据库schema变更
- ✅ 向后兼容（没有task_parameters的旧响应仍然工作）

## 验证命令

```bash
# 1. 编译任务
curl -X POST http://localhost:8090/api/agent/compile \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成一个贷款对比视频"}'

# 查看响应中的 task_parameters 字段

# 2. 验证参数清理
# 编译应该返回清理好的 kwargs，仅包含manifest中定义的参数
```

## 后续优化方向

1. **参数验证提示** - 在编译错误时显示哪些参数不被接受
2. **参数类型转换** - 自动根据参数类型（int/float/str）转换UI值
3. **参数说明展示** - 在参数旁显示manifest中的description字段
4. **参数选项渲染** - 如果参数有预定义选项，用下拉菜单代替文本框
