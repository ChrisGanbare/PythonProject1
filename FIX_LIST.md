# v2.3 问题修复清单

**测试日期**: 2026-03-24  
**通过率**: 53.8% (7/13)  
**状态**: 🔄 修复中

---

## 🐛 问题列表

### P0: 视频生成失败

**错误**:
```
Invalid value of type 'builtins.str' received for the 'orientation' property of bar
Received value: 'horizontal'
The 'orientation' property is an enumeration that may be specified as:
  - One of the following enumeration values: ['v', 'h']
```

**原因**: v2_renderer 中 orientation 参数传递错误

**修复**:
- [ ] 修改 core/v2_renderer.py
- [ ] orientation 应该是 'v' 或 'h'，不是 'horizontal'

---

### P1: 静态文件路由问题

**问题**:
- AI 编译页面 404
- 项目管理页面 404
- 代码工坊页面 404

**原因**: Dashboard 没有正确映射静态文件

**修复**:
- [ ] 添加静态文件路由
- [ ] 或者在 dashboard.py 中添加路由

---

### P2: v1 API 缺失

**问题**:
- GET /api/v1/templates - 404
- GET /api/v1/themes - 404

**原因**: v1 API 没有这些端点

**修复**:
- [ ] 添加兼容端点
- [ ] 或者前端改用 v2 API

---

## 🔧 修复进度

| 问题 | 优先级 | 状态 | 预计时间 |
|------|--------|------|----------|
| 视频生成 orientation | P0 | 🔄 修复中 | 5 分钟 |
| 静态文件路由 | P1 | ⏳ 待修复 | 10 分钟 |
| v1 API 缺失 | P2 | ⏳ 待修复 | 10 分钟 |

---

**最后更新**: 2026-03-24 21:30
