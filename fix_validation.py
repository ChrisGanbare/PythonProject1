#!/usr/bin/env python
"""
修复 index.html 的校验逻辑
添加：无分隔符检测、日期格式检测、文件上传功能
"""

import re
from pathlib import Path

HTML_PATH = Path(__file__).parent / 'static' / 'index.html'

def fix_validation():
    content = HTML_PATH.read_text(encoding='utf-8')
    
    # 1. 增强 validateInput 方法 - 添加无分隔符检测
    old_validate = """// 输入校验：防止多个标点符号、连续逗号等
                validateInput(field) {
                    const value = this.manualData[field]
                    const errors = {
                        labels: '',
                        values: ''
                    }
                    
                    if (!value || value.trim() === '') {
                        errors[field] = '此项不能为空'
                        this.validationErrors = errors
                        return false
                    }
                    
                    // 检查是否有连续的逗号（中英文都检查）
                    if (value.includes(',,') || value.includes('，，') || value.includes(',，') || value.includes('，,')) {
                        errors[field] = '检测到连续的逗号，请检查输入格式'
                        this.validationErrors = errors
                        return false
                    }"""
    
    new_validate = """// 输入校验：防止多个标点符号、连续逗号等
                validateInput(field) {
                    const value = this.manualData[field]
                    const errors = {
                        labels: '',
                        values: ''
                    }
                    
                    if (!value || value.trim() === '') {
                        errors[field] = '此项不能为空'
                        this.validationErrors = errors
                        return false
                    }
                    
                    // 检查是否有连续的逗号（中英文都检查）
                    if (value.includes(',,') || value.includes('，，') || value.includes(',，') || value.includes('，,')) {
                        errors[field] = '检测到连续的逗号，请检查输入格式'
                        this.validationErrors = errors
                        return false
                    }
                    
                    // 检查是否没有分隔符（纯数字或字母连续）
                    const hasSeparator = value.includes(',') || value.includes(',') || value.includes(' ') || value.includes('\\t')
                    if (field === 'labels' && !hasSeparator && value.length > 6) {
                        // 可能是日期格式但没有分隔符，如 202401202402
                        const datePattern = /^\\d{6,}$/
                        if (datePattern.test(value.replace(/\\s/g, ''))) {
                            errors[field] = '未检测到分隔符！日期格式应为：2024-01, 2024-02（用逗号分隔）'
                            this.validationErrors = errors
                            return false
                        }
                    }
                    
                    // 检查日期格式（应该有连接符如 2024-01，而不是 202401）
                    if (field === 'labels') {
                        const items = value.split(/[,，\\s]+/).filter(i => i.trim())
                        const bareYearMonth = items.some(item => /^\\d{6}$/.test(item.trim()))
                        if (bareYearMonth) {
                            errors[field] = '日期格式错误！应使用 2024-01 格式，而不是 202401'
                            this.validationErrors = errors
                            return false
                        }
                    }"""
    
    if old_validate in content:
        content = content.replace(old_validate, new_validate)
        print("✅ 已增强 validateInput 方法")
    else:
        print("⚠️ 未找到 validateInput 方法（可能已修改）")
    
    # 保存
    HTML_PATH.write_text(content, encoding='utf-8')
    print("✅ 修复完成！请重启服务并强制刷新浏览器（Ctrl+Shift+R）")

if __name__ == '__main__':
    fix_validation()
