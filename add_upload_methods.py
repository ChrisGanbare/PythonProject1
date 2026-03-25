#!/usr/bin/env python
"""
添加文件上传方法到 index.html
"""

from pathlib import Path

HTML_PATH = Path(__file__).parent / 'static' / 'index.html'

def add_upload_methods():
    content = HTML_PATH.read_text(encoding='utf-8')
    
    # 在 methods 开头添加文件上传方法
    old_methods = """methods: {
                // 输入校验：防止多个标点符号、连续逗号等"""
    
    new_methods = """methods: {
                // 触发文件上传
                triggerFileUpload() {
                    document.getElementById('fileUpload').click()
                },
                
                // 处理文件上传
                handleFileUpload(event) {
                    const file = event.target.files[0]
                    if (!file) {
                        this.uploadError = '未选择文件'
                        this.uploadedFile = null
                        return
                    }
                    
                    const fileExt = file.name.split('.').pop().toLowerCase()
                    if (!['csv', 'xlsx', 'xls'].includes(fileExt)) {
                        this.uploadError = '不支持的文件格式，请上传 CSV 或 Excel 文件'
                        this.uploadedFile = null
                        return
                    }
                    
                    if (file.size > 10 * 1024 * 1024) {
                        this.uploadError = '文件过大，请上传小于 10MB 的文件'
                        this.uploadedFile = null
                        return
                    }
                    
                    this.uploadError = ''
                    this.uploadedFile = {
                        name: file.name,
                        size: file.size
                    }
                },
                
                // 下载模板
                downloadTemplate() {
                    const csvContent = '日期，数值，系列名称\\n2024-01,100，销售额\\n2024-02,150，销售额\\n2024-03,200，销售额\\n2024-04,180，销售额'
                    const blob = new Blob(['\\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
                    const link = document.createElement('a')
                    link.href = URL.createObjectURL(blob)
                    link.download = '数据模板.csv'
                    link.click()
                },
                
                // 输入校验：防止多个标点符号、连续逗号等"""
    
    if old_methods in content:
        content = content.replace(old_methods, new_methods)
        print("✅ 已添加文件上传方法")
    else:
        print("⚠️ 未找到 methods 位置（可能已修改）")
    
    # 保存
    HTML_PATH.write_text(content, encoding='utf-8')
    print("✅ 修复完成！")

if __name__ == '__main__':
    add_upload_methods()
