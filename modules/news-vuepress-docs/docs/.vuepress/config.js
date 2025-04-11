import { viteBundler } from '@vuepress/bundler-vite'
import { defaultTheme } from '@vuepress/theme-default'
import { defineUserConfig } from 'vuepress'
import { path } from '@vuepress/utils'

export default defineUserConfig({
    base: '/NewsAggregator-test12/',

    // 添加客户端配置文件路径
    clientConfigFile: path.resolve(__dirname, './client.js'),

    lang: 'zh-CN',
    title: '人民日报新闻智能聚合系统',
    description: '人民日报新闻智能聚合系统文档',

    head: [
        // 站点图标
        ["link", { rel: "icon", href: "/ico/main-logo.svg" }],
    ],
    
    plugins: [

    ],
    
    bundler: viteBundler(),

    theme: defaultTheme({
        logo: '/ico/main-logo.svg',
        editLink: false,
        
        // 导航栏 - 简化后只保留与项目需求相关的选项
        navbar: [
            {
                text: '首页',
                link: '/',
            },
            {
                text: '今日新闻',
                link: '/today/',
            }
        ],
        
        repo: "https://github.com/fox142857/NewsAggregator-test12",
        repoLabel: '查看源码',
    }),
})