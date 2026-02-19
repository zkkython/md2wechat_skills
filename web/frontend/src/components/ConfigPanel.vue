<template>
  <div class="config-panel">
    <h3 class="panel-title">发布配置</h3>

    <div class="form-group">
      <label>视觉风格</label>
      <select v-model="model.style">
        <option value="academic_gray">学术灰</option>
        <option value="festival">节日快乐</option>
        <option value="tech">科技蓝</option>
        <option value="announcement">警示橙红</option>
      </select>
      <span class="hint">{{ styleHint }}</span>
    </div>

    <div class="form-group">
      <label>文章类型</label>
      <select v-model="model.articleType">
        <option value="news">普通文章</option>
        <option value="newspic">小绿书</option>
      </select>
    </div>

    <div class="form-group">
      <label>作者名称</label>
      <input
        v-model="model.author"
        type="text"
        placeholder="可选，默认为空"
      />
    </div>

    <div class="form-group checkbox">
      <label>
        <input v-model="model.comment" type="checkbox" />
        开启评论
      </label>
    </div>

    <div class="form-group checkbox indent" v-if="model.comment">
      <label>
        <input v-model="model.fansOnlyComment" type="checkbox" />
        仅粉丝可评论
      </label>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const model = defineModel()

const styleHint = computed(() => {
  const hints = {
    academic_gray: '简洁专业，适合技术文档',
    festival: '温暖红金，适合节日祝福',
    tech: '现代蓝调，适合产品介绍',
    announcement: '醒目突出，适合重要通知'
  }
  return hints[model.value.style]
})
</script>

<style scoped>
.config-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}

.form-group select,
.form-group input[type="text"] {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group select:focus,
.form-group input[type="text"]:focus {
  outline: none;
  border-color: #07c160;
}

.hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-group.checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #07c160;
}

.form-group.indent {
  padding-left: 24px;
}
</style>
