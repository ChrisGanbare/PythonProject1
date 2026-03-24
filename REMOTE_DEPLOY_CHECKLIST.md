# 📦 PythonProject1 - 远程部署检查清单

## ✅ 部署前检查

- [ ] 已安装 Python 3.9+
- [ ] 已克隆项目
- [ ] 已安装依赖 (`pip install -r requirements.txt`)
- [ ] 已配置防火墙 (端口 8000 和 8090)

## 🚀 启动服务

### API 服务
```bash
python start.py api --host 0.0.0.0 --port 8000
```

### Dashboard 控制台
```bash
python start.py dashboard --host 0.0.0.0 --port 8090
```

## 🌐 远程访问

- **API 文档**: `http://<服务器 IP>:8000/docs`
- **Dashboard**: `http://<服务器 IP>:8090`

## 📝 验证步骤

1. [ ] 访问 API 文档页面
2. [ ] 访问 Dashboard 页面
3. [ ] 测试创建视频作业
4. [ ] 检查日志无错误

## 🔧 故障排查

详见 `DEPLOY.md` 文档。

---

**祝部署顺利！** 🎉
