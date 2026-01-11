<template>
  <div class="settings-page">
    <div class="card">
      <h2 class="card-title">
        <i class="icon">⚙️</i> 系统设置
      </h2>
      
      <div class="settings-content">
        <div class="setting-group">
          <h3>模型配置</h3>
          <div class="form-list">
            <div class="form-row">
              <label for="model-dir" class="form-label">模型文件夹路径</label>
              <input 
                id="model-dir" 
                v-model="config.model_dir" 
                type="text" 
                placeholder="请输入模型文件夹路径"
                @change="saveConfig"
                class="form-input"
              />
            </div>
            
            <div class="form-row">
              <label for="context-length" class="form-label">上下文长度</label>
              <input 
                id="context-length" 
                v-model.number="config.context_length" 
                type="number" 
                min="512"
                max="4096"
                @change="saveConfig"
                class="form-input"
              />
            </div>
            
            <div class="form-row">
              <label for="max-tokens" class="form-label">最大Token数</label>
              <input 
                id="max-tokens" 
                v-model.number="config.max_tokens" 
                type="number" 
                min="128"
                max="1024"
                @change="saveConfig"
                class="form-input"
              />
            </div>
          </div>
        </div>
        
        <div class="setting-group">
          <h3>百度翻译API配置</h3>
          <div class="form-list">
            <div class="form-row">
              <label for="baidu-appid" class="form-label">App ID</label>
              <input 
                id="baidu-appid" 
                v-model="config.baidu_appid" 
                type="text" 
                placeholder="请输入百度翻译API的App ID"
                @change="saveConfig"
                class="form-input"
              />
            </div>
            
            <div class="form-row">
              <label for="baidu-appkey" class="form-label">App Key</label>
              <input 
                id="baidu-appkey" 
                v-model="config.baidu_appkey" 
                type="password" 
                placeholder="请输入百度翻译API的App Key"
                @change="saveConfig"
                class="form-input"
              />
            </div>
          </div>
        </div>
        
        <div class="setting-group">
          <h3>辅助功能</h3>
          <div class="checkbox-options">
            <label class="checkbox-group">
              <input 
                v-model="config.auto_copy" 
                type="checkbox"
                @change="saveConfig"
              />
              <span class="checkbox-label">自动复制翻译结果</span>
            </label>
          </div>
        </div>
      </div>
      
      <div class="action-bar">
        <button @click="saveConfig" class="btn btn-primary">
          <span>💾</span> 保存设置
        </button>
        <button @click="resetConfig" class="btn btn-secondary">
          <span>🔄</span> 恢复默认
        </button>
      </div>
      
      <Transition name="slide-fade">
        <div v-if="message" class="notification-toast" :class="{'error': errorMessage}">
          <span class="notification-icon">{{ errorMessage ? '❌' : '✅' }}</span>
          <span class="notification-message">{{ message }}</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';

export default {
  name: 'Settings',
  setup() {
    const config = ref({});
    const message = ref('');
    const errorMessage = ref(false);
    let messageTimeout = null;
    
    // 加载配置（带重试机制）
    const loadConfig = async (retries = 30, delay = 500) => {
      for (let i = 0; i < retries; i++) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 2000);
          
          const response = await fetch('http://127.0.0.1:8000/config', {
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            const data = await response.json();
            if (data.success) {
              config.value = { ...data.config };
              showMessage('配置加载成功', false);
              return; // 成功连接，退出
            } else {
              showMessage('获取配置失败', true);
              return;
            }
          } else {
            if (i < retries - 1) {
              await new Promise(resolve => setTimeout(resolve, delay));
              continue;
            }
            showMessage('网络错误，无法获取配置', true);
            return;
          }
        } catch (error) {
          // 连接失败，继续重试
          if (i < retries - 1) {
            await new Promise(resolve => setTimeout(resolve, delay));
            continue;
          }
          // 最后一次尝试失败，使用默认配置
          if (import.meta.env.DEV && error.name !== 'AbortError') {
            console.warn('无法连接到后端服务器，使用默认配置');
          }
          // 设置默认配置
          config.value = {
            model_dir: './models',
            current_model: '',
            context_length: 2048,
            baidu_appid: '',
            baidu_appkey: '',
            threads: 4,
            max_tokens: 512,
            temperature: 0.1,
            api_base_url: 'http://127.0.0.1:8000',
            timeout: 5000,
            auto_copy: false,
            dark_mode: false,
            theme_color: '#6366f1'
          };
          // 不显示消息，使用默认配置
        }
      }
    };
    
    // 保存配置
    const saveConfig = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/config', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config.value)
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            showMessage(data.message || '配置已保存', false);
          } else {
            showMessage('保存配置失败', true);
          }
        } else {
          showMessage('网络错误，无法保存配置', true);
        }
      } catch (error) {
        console.error('保存配置失败:', error);
        showMessage(`保存配置失败: ${error.message}`, true);
      }
    };
    
    // 显示消息（自动消失）
    const showMessage = (msg, isError = false) => {
      // 清除之前的定时器
      if (messageTimeout) {
        clearTimeout(messageTimeout);
      }
      
      message.value = msg;
      errorMessage.value = isError;
      
      // 3秒后自动消失
      messageTimeout = setTimeout(() => {
        message.value = '';
        errorMessage.value = false;
      }, 3000);
    };
    
    // 恢复默认配置
    const resetConfig = () => {
      config.value = {
        model_dir: './models',
        current_model: '',
        context_length: 2048,
        threads: 4,
        max_tokens: 512,
        temperature: 0.1,
        api_base_url: 'http://127.0.0.1:8000',
        timeout: 5000,
        auto_copy: false,
        dark_mode: false,
        theme_color: '#6366f1'
      };
      showMessage('已恢复默认配置，请记得保存', false);
    };
    
    // 页面加载时获取配置
    onMounted(async () => {
      await loadConfig();
    });
    
    // 组件卸载时清理定时器
    onUnmounted(() => {
      if (messageTimeout) {
        clearTimeout(messageTimeout);
      }
    });
    
    return {
      config,
      message,
      errorMessage,
      saveConfig,
      resetConfig
    };
  }
};
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
  min-height: 0;
}

.card {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  flex: 1;
  padding: 16px;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
}

.setting-group {
  margin-bottom: 16px;
}

.setting-group:last-child {
  margin-bottom: 0;
}

.setting-group h3 {
  margin: 0 0 10px 0;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 700;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--border-color);
  letter-spacing: -0.2px;
}

.form-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.form-label {
  flex: 0 0 140px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.8rem;
  letter-spacing: 0.1px;
  text-align: right;
}

.form-input {
  flex: 0 1 400px;
  max-width: 400px;
  padding: 10px 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  transition: all 0.2s ease;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: inherit;
}

.form-input:hover {
  border-color: var(--border-hover);
  background-color: var(--bg-secondary);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
  background-color: var(--bg-primary);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-group label {
  display: block;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.75rem;
  letter-spacing: 0.1px;
}

.input-group input,
.input-group select,
.input-group textarea {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  transition: var(--transition);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: inherit;
}

.input-group input[type="color"] {
  height: 50px;
  cursor: pointer;
  padding: 4px;
}

.input-group input[type="number"] {
  -moz-appearance: textfield;
}

.input-group input[type="number"]::-webkit-outer-spin-button,
.input-group input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.input-group select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 14px center;
  background-repeat: no-repeat;
  background-size: 18px;
  padding-right: 44px;
  cursor: pointer;
}

[data-theme="dark"] .input-group select {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23cbd5e1' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
}

.input-group input:focus,
.input-group select:focus,
.input-group textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.theme-item {
  flex: 1;
}

.radio-group {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
  background: var(--bg-primary);
}

.radio-group:hover {
  border-color: var(--primary-color);
  background: var(--bg-tertiary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.radio-group.active {
  border-color: var(--primary-color);
  background: var(--primary-light);
}

.radio-group input[type="radio"] {
  width: 16px;
  height: 16px;
  margin: 0;
  cursor: pointer;
  accent-color: var(--primary-color);
}

.radio-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.8rem;
  flex: 1;
}

.checkbox-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
  background: var(--bg-primary);
}

.checkbox-group:hover {
  border-color: var(--primary-color);
  background: var(--bg-tertiary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.checkbox-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin: 0;
  cursor: pointer;
  accent-color: var(--primary-color);
}

.checkbox-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.8rem;
  flex: 1;
}

.action-bar {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  margin-top: 16px;
  border-top: 2px solid var(--border-color);
  flex-shrink: 0;
}

.action-bar .btn {
  padding: 10px 20px;
  font-size: 0.85rem;
  font-weight: 600;
  min-width: 120px;
}

/* 右上角弹出通知 */
.notification-toast {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.9rem;
  border: 2px solid;
  box-shadow: var(--shadow-lg);
  min-width: 200px;
  max-width: 400px;
  backdrop-filter: blur(10px);
}

.notification-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.notification-message {
  flex: 1;
  word-break: break-word;
}

.notification-toast.error {
  background-color: rgba(239, 68, 68, 0.95);
  color: white;
  border-color: rgba(239, 68, 68, 0.5);
}

[data-theme="dark"] .notification-toast.error {
  background-color: rgba(239, 68, 68, 0.9);
  border-color: rgba(239, 68, 68, 0.6);
}

.notification-toast:not(.error) {
  background-color: rgba(16, 185, 129, 0.95);
  color: white;
  border-color: rgba(16, 185, 129, 0.5);
}

[data-theme="dark"] .notification-toast:not(.error) {
  background-color: rgba(16, 185, 129, 0.9);
  border-color: rgba(16, 185, 129, 0.6);
}

/* 过渡动画 */
.slide-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(100%) translateY(0);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(100%) translateY(0);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .form-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .form-label {
    flex: none;
    text-align: left;
    width: 100%;
  }
  
  .form-input {
    flex: 1;
    max-width: 100%;
    width: 100%;
  }
  
  .form-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .action-bar {
    flex-direction: column;
  }
  
  .action-bar .btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .settings-page {
    gap: 20px;
  }
  
  .setting-group h3 {
    font-size: 1.15rem;
  }
  
  .form-grid {
    gap: 18px;
  }
  
  .checkbox-group {
    padding: 14px;
  }
}
</style>