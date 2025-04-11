<template>
  <div>
    <AllVersions 
      :title="title" 
      :date="date" 
      :versions="versions" 
      v-if="loaded" 
    />
    <div v-else class="loading">
      <p>正在加载新闻数据...</p>
    </div>
  </div>
</template>

<script>
import AllVersions from './AllVersions.vue'

export default {
  name: 'NewsFetcher',
  components: {
    AllVersions
  },
  data() {
    return {
      title: '人民日报 - 今日新闻',
      date: '2025-04-08',
      versions: [],
      loaded: false
    }
  },
  mounted() {
    // 在组件挂载后加载数据
    this.loadNewsData();
  },
  methods: {
    loadNewsData() {
      // 使用Fetch API获取HTML文件
      fetch('/news/20250408.html')
        .then(response => {
          if (!response.ok) {
            throw new Error('获取新闻数据失败：' + response.statusText);
          }
          return response.text();
        })
        .then(html => {
          // 解析HTML内容
          this.parseNewsDataFromHtml(html);
          this.loaded = true;
        })
        .catch(error => {
          console.error('加载新闻数据失败:', error);
          // 如果加载失败，使用备用数据
          this.loadFallbackData();
          this.loaded = true;
        });
    },
    
    parseNewsDataFromHtml(html) {
      try {
        // 创建一个临时DOM元素来解析HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // 获取标题和日期
        const headerTitle = doc.querySelector('.header h1');
        if (headerTitle) {
          this.title = headerTitle.textContent;
        }
        
        // 提取所有版面数据
        const versionElements = doc.querySelectorAll('.version');
        this.versions = Array.from(versionElements).map(versionElement => {
          // 获取版面标题
          const titleElement = versionElement.querySelector('.version-title');
          const title = titleElement ? titleElement.textContent : '未知版面';
          
          // 获取新闻列表
          const newsItems = versionElement.querySelectorAll('.news-item');
          const news = Array.from(newsItems).map(item => {
            const linkElement = item.querySelector('.news-link');
            return {
              title: linkElement ? linkElement.textContent : '未知新闻',
              url: linkElement ? linkElement.getAttribute('href') : '#'
            };
          });
          
          return { title, news };
        });
      } catch (error) {
        console.error('解析HTML数据失败:', error);
        this.loadFallbackData();
      }
    },
    
    loadFallbackData() {
      // 备用数据，当无法从HTML文件加载时使用
      this.versions = [
        {
          title: '01版：要闻',
          news: [
            { title: '中共中央国务院印发《加快建设农业强国规划（2024—2035年）》', url: 'http://paper.people.com.cn/rmrb/pc/content/202504/08/content_30066500.html' },
            { title: '推动学习教育入脑入心见行见效（锲而不舍落实中央八项规定精神）', url: 'http://paper.people.com.cn/rmrb/pc/content/202504/08/content_30066501.html' },
            { title: '赵乐际同芬兰议长哈拉—阿霍举行会谈', url: 'http://paper.people.com.cn/rmrb/pc/content/202504/08/content_30066502.html' },
            // 更多新闻...
          ]
        },
        {
          title: '02版：要闻',
          news: [
            { title: '抓紧补齐防汛减灾短板弱项  全力防范洪涝干旱灾害风险', url: 'http://paper.people.com.cn/rmrb/pc/content/202504/08/content_30066508.html' },
            { title: '分阶段科学谋划推进农业强国建设（政策解读）', url: 'http://paper.people.com.cn/rmrb/pc/content/202504/08/content_30066509.html' },
            // 更多新闻...
          ]
        },
        // 更多版面...
      ];
    }
  }
}
</script>

<style scoped>
.loading {
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #666;
}
</style> 