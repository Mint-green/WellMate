<template>
  <view class="markdown-content">
    <block v-for="(element, index) in parsedElements" :key="index">
      <!-- 标题 -->
      <view v-if="element.type === 'heading'" :class="'markdown-heading-' + element.level">
        {{ element.content }}
      </view>
      
      <!-- 段落 -->
      <view v-else-if="element.type === 'paragraph'" class="markdown-paragraph">
        <block v-for="(child, childIndex) in element.children" :key="childIndex">
          <text v-if="child.type === 'text'" class="markdown-text">{{ child.content }}</text>
          <text v-else-if="child.type === 'bold'" class="markdown-bold">{{ child.content }}</text>
          <text v-else-if="child.type === 'italic'" class="markdown-italic">{{ child.content }}</text>
          <text v-else-if="child.type === 'inline-code'" class="markdown-inline-code">{{ child.content }}</text>
          <text v-else-if="child.type === 'strikethrough'" class="markdown-strikethrough">{{ child.content }}</text>
          <text v-else-if="child.type === 'link'" class="markdown-link" @click="handleLinkClick(child.url)">{{ child.content }}</text>
        </block>
      </view>
      
      <!-- 代码块 -->
      <view v-else-if="element.type === 'code'" class="markdown-code-block">
        {{ element.content }}
      </view>
      
      <!-- 引用 -->
      <view v-else-if="element.type === 'blockquote'" class="markdown-blockquote">
        {{ element.content }}
      </view>
      
      <!-- 无序列表 -->
      <view v-else-if="element.type === 'unordered-list'" class="markdown-unordered-list">
        <view v-for="(item, itemIndex) in element.items" :key="itemIndex" class="markdown-list-item">
          <text class="markdown-list-bullet">•</text>
          <text>{{ item }}</text>
        </view>
      </view>
      
      <!-- 有序列表 -->
      <view v-else-if="element.type === 'ordered-list'" class="markdown-ordered-list">
        <view v-for="(item, itemIndex) in element.items" :key="itemIndex" class="markdown-list-item">
          <text class="markdown-list-number">{{ itemIndex + 1 }}.</text>
          <text>{{ item }}</text>
        </view>
      </view>
      
      <!-- 图片 -->
      <image v-else-if="element.type === 'image'" :src="element.url" :alt="element.alt" class="markdown-image" mode="widthFix"></image>
      
      <!-- 分隔线 -->
      <view v-else-if="element.type === 'hr'" class="markdown-hr"></view>
      
      <!-- 换行 -->
      <view v-else-if="element.type === 'br'"></view>
    </block>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  content: {
    type: String,
    required: true
  }
})

// 处理链接点击事件
const handleLinkClick = (url) => {
  // 在实际应用中，你可能需要根据链接类型进行不同的处理
  // 这里简单地尝试打开链接
  try {
    // 如果是外部链接，可以使用浏览器打开
    if (url.startsWith('http')) {
      // 注意：在小程序中，需要在 app.json 中配置允许的域名
      uni.navigateTo({
        url: `/pages/webview/webview?url=${encodeURIComponent(url)}`
      })
    } else {
      // 内部链接跳转
      uni.navigateTo({
        url: url
      })
    }
  } catch (error) {
    console.error('Failed to open link:', error)
    uni.showToast({
      title: '无法打开链接',
      icon: 'none'
    })
  }
}

// 解析Markdown内容为元素数组
const parsedElements = computed(() => {
  if (!props.content) return []
  
  const elements = []
  const lines = props.content.split('\n')
  let inCodeBlock = false
  let codeContent = ''
  let codeLang = ''
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    // 处理代码块
    if (/^```/.test(line)) {
      if (!inCodeBlock) {
        // 开始代码块
        inCodeBlock = true
        codeLang = line.replace(/^```/, '').trim()
        codeContent = ''
      } else {
        // 结束代码块
        inCodeBlock = false
        elements.push({
          type: 'code',
          lang: codeLang,
          content: codeContent.trim()
        })
        codeContent = ''
        codeLang = ''
      }
      continue
    }
    
    // 如果在代码块中，收集代码内容
    if (inCodeBlock) {
      codeContent += line + '\n'
      continue
    }
    
    // 处理空行
    if (line.trim() === '') {
      elements.push({
        type: 'br'
      })
      continue
    }
    
    // 标题 (# H1, ## H2, ### H3 等)
    if (/^#{1,6}\s/.test(line)) {
      const level = line.match(/^#+/)[0].length
      const content = line.replace(/^#+\s/, '')
      elements.push({
        type: 'heading',
        level: level,
        content: content
      })
    }
    
    // 分隔线
    else if (/^---|^___|^\*\*\*/.test(line)) {
      elements.push({
        type: 'hr'
      })
    }
    
    // 引用块
    else if (/^>\s/.test(line)) {
      const content = line.replace(/^>\s/, '')
      elements.push({
        type: 'blockquote',
        content: content
      })
    }
    
    // 图片 (![alt](url))
    else if (/^!\[.*?\]\(.*?\)/.test(line)) {
      const imgRegex = /!\[(.*?)\]\((.*?)\)/
      const match = line.match(imgRegex)
      if (match) {
        elements.push({
          type: 'image',
          alt: match[1],
          url: match[2]
        })
      }
    }
    
    // 无序列表 (- 或 * 开头)
    else if (/^[\-\*]\s/.test(line)) {
      const items = []
      let j = i
      
      // 收集连续的列表项
      while (j < lines.length && /^[\-\*]\s/.test(lines[j])) {
        items.push(lines[j].replace(/^[\-\*]\s/, ''))
        j++
      }
      
      elements.push({
        type: 'unordered-list',
        items: items
      })
      
      // 跳过已处理的列表项
      i = j - 1
    }
    
    // 有序列表 (数字开头)
    else if (/^\d+\.\s/.test(line)) {
      const items = []
      let j = i
      
      // 收集连续的列表项
      while (j < lines.length && /^\d+\.\s/.test(lines[j])) {
        items.push(lines[j].replace(/^\d+\.\s/, ''))
        j++
      }
      
      elements.push({
        type: 'ordered-list',
        items: items
      })
      
      // 跳过已处理的列表项
      i = j - 1
    }
    
    // 普通段落
    else {
      // 处理行内Markdown语法
      let processedLine = line
      
      // 处理删除线 (~~text~~)
      processedLine = processedLine.replace(/~~(.*?)~~/g, (match, p1) => {
        return `{{strikethrough:${p1}}}`
      })
      
      // 处理链接 ([text](url))
      processedLine = processedLine.replace(/\[(.*?)\]\((.*?)\)/g, (match, p1, p2) => {
        return `{{link:${p1}:${p2}}}`
      })
      
      // 处理粗体 (**text** 或 __text__)
      processedLine = processedLine.replace(/\*\*(.*?)\*\*|__(.*?)__/g, (match, p1, p2) => {
        const content = p1 || p2
        return content ? `{{bold:${content}}}` : match
      })
      
      // 处理斜体 (*text* 或 _text_)
      processedLine = processedLine.replace(/\*(.*?)\*|_(.*?)_/g, (match, p1, p2) => {
        return `{{italic:${p1 || p2}}}`
      })
      
      // 处理行内代码 (`code`)
      processedLine = processedLine.replace(/`(.*?)`/g, (match, p1) => {
        return `{{inline-code:${p1}}}`
      })
      
      // 将处理后的段落分割为元素
      const segments = processedLine.split(/(\{\{.*?\}\})/)
      
      if (segments.length > 1) {
        // 包含行内格式的段落
        const paragraphElements = []
        segments.forEach(segment => {
          if (segment.startsWith('{{') && segment.endsWith('}}')) {
            // 格式化元素
            const formatMatch = segment.match(/\{\{(.*?):(.*)\}\}/)
            if (formatMatch) {
              const type = formatMatch[1]
              const content = formatMatch[2]
              
              if (type === 'link') {
                // 链接格式: {{link:text:url}}
                const [displayText, url] = content.split(':')
                paragraphElements.push({
                  type: 'link',
                  content: displayText,
                  url: url
                })
              } else {
                paragraphElements.push({
                  type: type,
                  content: content
                })
              }
            }
          } else if (segment !== '') {
            // 普通文本
            paragraphElements.push({
              type: 'text',
              content: segment
            })
          }
        })
        
        elements.push({
          type: 'paragraph',
          children: paragraphElements
        })
      } else {
        // 普通段落
        elements.push({
          type: 'paragraph',
          children: [{
            type: 'text',
            content: line
          }]
        })
      }
    }
  }
  
  return elements
})
</script>

<style scoped>
.markdown-content {
  display: flex;
  flex-direction: column;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  width: 100%;
}

.markdown-heading-1 {
  font-size: 36rpx;
  font-weight: bold;
  margin: 20rpx 0 10rpx 0;
  color: #333;
}

.markdown-heading-2 {
  font-size: 32rpx;
  font-weight: bold;
  margin: 18rpx 0 9rpx 0;
  color: #333;
}

.markdown-heading-3 {
  font-size: 28rpx;
  font-weight: bold;
  margin: 16rpx 0 8rpx 0;
  color: #333;
}

.markdown-heading-4 {
  font-size: 26rpx;
  font-weight: bold;
  margin: 14rpx 0 7rpx 0;
  color: #333;
}

.markdown-heading-5 {
  font-size: 24rpx;
  font-weight: bold;
  margin: 12rpx 0 6rpx 0;
  color: #333;
}

.markdown-heading-6 {
  font-size: 22rpx;
  font-weight: bold;
  margin: 10rpx 0 5rpx 0;
  color: #333;
}

.markdown-paragraph {
  font-size: 28rpx;
  line-height: 1.6;
  margin: 10rpx 0;
  color: #333;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  width: 100%;
}

.markdown-text {
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}

.markdown-bold {
  font-weight: bold;
}

.markdown-italic {
  font-style: italic;
}

.markdown-strikethrough {
  text-decoration: line-through;
}

.markdown-inline-code {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 2rpx 8rpx;
  border-radius: 4rpx;
  font-size: 24rpx;
}

.markdown-code-block {
  font-family: monospace;
  background-color: #f8f8f8;
  padding: 20rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
  line-height: 1.5;
  margin: 15rpx 0;
  white-space: pre-wrap;
  overflow-x: auto;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
}

.markdown-blockquote {
  border-left: 6rpx solid #ddd;
  padding-left: 20rpx;
  margin: 15rpx 0;
  color: #666;
  font-style: italic;
}

.markdown-hr {
  height: 1rpx;
  background-color: #ddd;
  margin: 20rpx 0;
}

.markdown-unordered-list {
  margin: 10rpx 0;
  padding-left: 40rpx;
}

.markdown-ordered-list {
  margin: 10rpx 0;
  padding-left: 40rpx;
}

.markdown-list-item {
  display: flex;
  flex-direction: row;
  margin: 8rpx 0;
  font-size: 28rpx;
  line-height: 1.5;
  color: #333;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}

.markdown-list-bullet {
  margin-right: 15rpx;
  min-width: 20rpx;
}

.markdown-list-number {
  margin-right: 15rpx;
  min-width: 30rpx;
}

.markdown-link {
  color: #007AFF;
  text-decoration: underline;
}

.markdown-image {
  max-width: 100%;
  margin: 10rpx 0;
  border-radius: 8rpx;
}
</style>