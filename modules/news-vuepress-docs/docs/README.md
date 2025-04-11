---
home: true
title: 人民日报新闻智能聚合系统
description: 自动爬取人民日报当天内容的智能聚合平台
heroImage: /ico/main-logo.svg
actions:
  - text: 浏览今日新闻
    link: /today/
    type: primary
features:
  - title: 实时更新
    details: 每日自动爬取人民日报最新内容
  - title: 清晰分类
    details: 按照版面进行分类，便于浏览
  - title: 原文链接
    details: 提供返回原文的便捷链接
footer: 人民日报新闻智能聚合系统 | Copyright © 2025
---

<!-- <script>
export default {
  mounted () {
    // 自动重定向到今日新闻页面
    window.location.href = '/today/'
  }
}
</script> -->

# 人民日报新闻智能聚合系统

## 项目简介

人民日报新闻智能聚合系统是一个自动化的新闻采集、处理和发布平台，专注于从人民日报网站获取最新新闻，并通过AI技术生成摘要，最终以静态网站形式发布。

## 核心功能

- **自动新闻采集**：定时从人民日报网站抓取最新新闻
- **AI摘要生成**：利用多种AI API自动生成新闻摘要
- **Markdown转换**：将HTML内容标准化转换为Markdown格式
- **静态站点生成**：基于VuePress框架生成现代化的新闻浏览网站
- **自动化部署**：集成Gitee API实现自动化发布
- **多维度索引**：支持时间、分类、标签等多种方式浏览新闻