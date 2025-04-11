<template>
  <div class="all-versions-container">
    <h1 class="main-title">{{ title }}</h1>
    <p class="date">{{ date }}</p>
    
    <div class="versions">
      <div v-for="(version, index) in versions" :key="index" class="version-card">
        <h2 class="version-title">{{ version.title }}</h2>
        <ul class="news-list">
          <li v-for="(news, newsIndex) in version.news" :key="newsIndex" class="news-item">
            <a :href="news.url" target="_blank" class="news-link">{{ news.title }}</a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AllVersions',
  props: {
    title: {
      type: String,
      default: '人民日报 - 今日新闻'
    },
    date: {
      type: String,
      default: '2025-04-08'
    },
    versions: {
      type: Array,
      required: true
    }
  }
}
</script>

<style scoped>
.all-versions-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.main-title {
  text-align: center;
  font-size: 2rem;
  color: #c00;
  margin-bottom: 0.5rem;
}

.date {
  text-align: center;
  color: #666;
  margin-bottom: 2rem;
}

.versions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.version-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  transition: transform 0.3s;
}

.version-card:hover {
  transform: translateY(-5px);
}

.version-title {
  color: #c00;
  font-size: 1.25rem;
  padding-bottom: 10px;
  border-bottom: 2px solid #c00;
  margin-bottom: 15px;
}

.news-list {
  list-style-type: none;
  padding-left: 0;
}

.news-item {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dashed #eee;
}

.news-link {
  color: #333;
  text-decoration: none;
  font-size: 14px;
}

.news-link:hover {
  color: #c00;
}

@media (max-width: 768px) {
  .versions {
    grid-template-columns: 1fr;
  }
}
</style> 