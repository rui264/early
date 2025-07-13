<template>
  <div id="app">
    <el-container>
      <!-- 头部 -->
      <el-header class="header">
        <h1>🤖 多智能体聊天系统</h1>
        <div class="header-controls">
          <el-select v-model="selectedModel" placeholder="选择模型" style="width: 150px; margin-right: 10px;">
            <el-option label="GPT-4 Turbo" value="gpt-4-turbo" />
            <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
            <el-option label="Qwen Turbo" value="qwen-turbo" />
          </el-select>
          <el-select v-model="selectedProvider" placeholder="选择提供商" style="width: 120px;">
            <el-option label="OpenAI" value="openai" />
            <el-option label="千问" value="qwen" />
          </el-select>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="300px" class="sidebar">
          <div class="session-controls">
            <el-input 
              v-model="sessionId" 
              placeholder="会话ID" 
              style="margin-bottom: 10px;"
            />
            <el-button type="primary" @click="newSession" style="width: 100%; margin-bottom: 10px;">
              新建会话
            </el-button>
            <el-button @click="clearHistory" style="width: 100%; margin-bottom: 20px;">
              清空历史
            </el-button>
          </div>

          <!-- 文件上传区域 -->
          <div class="upload-section">
            <h3>📁 知识库管理</h3>
            <el-upload
              ref="uploadRef"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :data="{ session_id: sessionId }"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              :auto-upload="false"
              accept=".pdf,.txt,.docx,.md"
              drag
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 PDF、TXT、DOCX、MD 格式文件
                </div>
              </template>
            </el-upload>
            <el-button type="success" @click="submitUpload" style="width: 100%; margin-top: 10px;">
              上传文件
            </el-button>
          </div>
        </el-aside>

        <!-- 主聊天区域 -->
        <el-main class="main-content">
          <div class="chat-container">
            <!-- 消息列表 -->
            <div class="messages" ref="messagesRef">
              <div 
                v-for="(message, index) in messages" 
                :key="index" 
                :class="['message', message.role]"
              >
                <div class="message-avatar">
                  <el-avatar :icon="message.role === 'user' ? 'User' : 'ChatDotRound'" />
                </div>
                <div class="message-content">
                  <div class="message-text">{{ message.content }}</div>
                  <div class="message-time" v-if="message.time">{{ message.time }}</div>
                </div>
              </div>
            </div>

            <!-- 输入区域 -->
            <div class="input-area">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="请输入您的问题..."
                @keydown.ctrl.enter="sendMessage"
              />
              <div class="input-controls">
                <el-button 
                  type="primary" 
                  @click="sendMessage" 
                  :loading="loading"
                  :disabled="!inputMessage.trim()"
                >
                  发送 (Ctrl+Enter)
                </el-button>
              </div>
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'App',
  data() {
    return {
      sessionId: 'default_session',
      selectedModel: 'gpt-4-turbo',
      selectedProvider: 'openai',
      inputMessage: '',
      messages: [],
      loading: false,
      uploadUrl: '/api/upload',
      uploadHeaders: {}
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    // 发送消息
    async sendMessage() {
      if (!this.inputMessage.trim() || this.loading) return

      const userMessage = {
        role: 'user',
        content: this.inputMessage,
        time: new Date().toLocaleString()
      }
      
      this.messages.push(userMessage)
      this.inputMessage = ''
      this.loading = true

      try {
        const response = await axios.post('/api/chat', {
          session_id: this.sessionId,
          question: userMessage.content,
          provider: this.selectedProvider,
          model: this.selectedModel
        })

        if (response.data.success) {
          this.messages.push({
            role: 'assistant',
            content: response.data.answer,
            time: response.data.question_time || new Date().toLocaleString()
          })
        } else {
          throw new Error('请求失败')
        }
      } catch (error) {
        ElMessage.error(`发送失败: ${error.message}`)
        console.error('发送消息失败:', error)
      } finally {
        this.loading = false
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },

    // 加载历史记录
    async loadHistory() {
      try {
        const response = await axios.get('/api/history', {
          params: { session_id: this.sessionId }
        })
        
        if (response.data.success) {
          this.messages = response.data.history.map(msg => ({
            role: msg.role,
            content: msg.content,
            time: msg.time
          }))
        }
      } catch (error) {
        console.error('加载历史记录失败:', error)
      }
    },

    // 新建会话
    newSession() {
      this.sessionId = `session_${Date.now()}`
      this.messages = []
      ElMessage.success('新建会话成功')
    },

    // 清空历史
    async clearHistory() {
      try {
        await ElMessageBox.confirm('确定要清空当前会话的历史记录吗？', '确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // 这里可以调用清空历史的API
        this.messages = []
        ElMessage.success('历史记录已清空')
      } catch (error) {
        // 用户取消
      }
    },

    // 滚动到底部
    scrollToBottom() {
      const messagesRef = this.$refs.messagesRef
      if (messagesRef) {
        messagesRef.scrollTop = messagesRef.scrollHeight
      }
    },

    // 文件上传相关方法
    beforeUpload(file) {
      const isValidType = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/markdown'].includes(file.type)
      if (!isValidType) {
        ElMessage.error('只支持 PDF、TXT、DOCX、MD 格式文件!')
        return false
      }
      return true
    },

    submitUpload() {
      this.$refs.uploadRef.submit()
    },

    handleUploadSuccess(response) {
      ElMessage.success('文件上传成功!')
      console.log('上传成功:', response)
    },

    handleUploadError(error) {
      ElMessage.error('文件上传失败!')
      console.error('上传失败:', error)
    }
  }
}
</script>

<style scoped>
#app {
  height: 100vh;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
}

.header-controls {
  display: flex;
  align-items: center;
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  padding: 20px;
}

.session-controls {
  margin-bottom: 30px;
}

.upload-section {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.upload-section h3 {
  margin-bottom: 15px;
  color: #606266;
}

.main-content {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 10px;
}

.message-content {
  max-width: 70%;
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.message.user .message-time {
  color: rgba(255,255,255,0.8);
}

.input-area {
  padding: 20px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

.input-controls {
  margin-top: 10px;
  text-align: right;
}

/* 滚动条样式 */
.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 