import { defineClientConfig } from '@vuepress/client'

export default defineClientConfig({
  enhance({ app }) {
    app.component('currentdate', {
      setup() {
        // 获取北京时间
        const now = new Date()
        const beijingOffset = 8 // 北京时间为UTC+8
        const utc = now.getTime() + (now.getTimezoneOffset() * 60000)
        const beijingTime = new Date(utc + (3600000 * beijingOffset))
        
        // 格式化日期为"YYYY年MM月DD日"
        const year = beijingTime.getFullYear()
        const month = String(beijingTime.getMonth() + 1).padStart(2, '0')
        const day = String(beijingTime.getDate()).padStart(2, '0')
        
        const dateString = `${year}年${month}月${day}日`
        
        return () => dateString
      }
    })
  }
})