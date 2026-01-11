<template>
  <div class="smart-translation">
    <div class="card">
      <h2 class="card-title">
        <i class="icon">🤖</i> 智能翻译
      </h2>
      
      <div class="controls-section">
        <!-- 目标语言 - 最左边 -->
        <div class="control-group lang-selector">
          <label for="target-lang" class="control-label">
            <span class="label-icon">🌐</span>
            <span class="label-text">目标语言</span>
          </label>
          <select id="target-lang" v-model="targetLang" @change="debouncedTranslate" class="modern-select">
            <option value="zh">🇨🇳 中文</option>
            <option value="en">🇺🇸 英语</option>
            <option value="ja">🇯🇵 日语</option>
            <option value="ko">🇰🇷 韩语</option>
            <option value="fr">🇫🇷 法语</option>
            <option value="de">🇩🇪 德语</option>
            <option value="es">🇪🇸 西班牙语</option>
            <option value="ru">🇷🇺 俄语</option>
            <option value="ar">🇸🇦 阿拉伯语</option>
          </select>
        </div>
        
        <!-- 翻译引擎切换 - 卡片式设计 -->
        <div class="engine-selector">
          <label class="control-label">
            <span class="label-icon">⚡</span>
            <span class="label-text">翻译引擎</span>
          </label>
          <div class="engine-toggle-group">
            <button 
              class="engine-toggle-btn" 
              :class="{ active: provider === 'llama-cpp' }"
              @click="provider = 'llama-cpp'; onProviderChange()"
            >
              <span class="btn-icon">🎯</span>
              <span class="btn-text">本地模型</span>
              <span class="btn-badge" v-if="provider === 'llama-cpp'">当前</span>
            </button>
            <button 
              class="engine-toggle-btn" 
              :class="{ active: provider === 'openai' || provider === 'baidu' }"
              @click="provider = 'openai'; onProviderChange()"
            >
              <span class="btn-icon">☁️</span>
              <span class="btn-text">云端API</span>
              <span class="btn-badge" v-if="provider === 'openai' || provider === 'baidu'">当前</span>
            </button>
          </div>
        </div>
        
        <!-- 翻译模型选择 - 仅当选择本地模型时显示 -->
        <div class="control-group model-selector" v-if="provider === 'llama-cpp'">
          <label for="model-select" class="control-label">
            <span class="label-icon">🤖</span>
            <span class="label-text">翻译模型</span>
          </label>
          <select 
            id="model-select" 
            v-model="selectedModel" 
            @change="switchModel" 
            :disabled="loadingModels"
            class="modern-select"
          >
            <option value="" disabled>{{ loadingModels ? '加载中...' : (models.length === 0 ? '未找到模型' : '请选择模型') }}</option>
            <option v-for="model in models" :key="model.name" :value="model.name">
              {{ model.name }} ({{ model.size_mb }} MB)
            </option>
          </select>
        </div>
        
        <!-- 服务商选择 - 仅当选择云端API时显示 -->
        <div class="control-group provider-selector" v-if="provider === 'openai' || provider === 'baidu'">
          <label for="provider-select" class="control-label">
            <span class="label-icon">🔌</span>
            <span class="label-text">服务商</span>
          </label>
          <select 
            id="provider-select" 
            v-model="apiProvider" 
            @change="onApiProviderChange"
            class="modern-select"
          >
            <option value="baidu">百度翻译</option>
          </select>
        </div>
      </div>
      
      <div class="translation-workspace">
        <div class="input-panel">
          <div class="panel-header">
            <h3>原文</h3>
            <div class="panel-actions">
              <button @click="clearInput" class="btn btn-secondary small">清空</button>
              <button @click="copyInput" class="btn btn-secondary small">复制</button>
            </div>
          </div>
          <div class="input-area">
            <textarea 
              id="source-text" 
              v-model="sourceText" 
              placeholder="请输入要翻译的文本..."
              @input="debouncedTranslate"
            ></textarea>
          </div>
        </div>
        
        <div class="output-panel">
          <div class="panel-header">
            <h3>译文</h3>
            <div class="panel-actions">
              <button @click="copyResult" class="btn btn-secondary small">复制</button>
              <button @click="speakResult" class="btn btn-secondary small">朗读</button>
            </div>
          </div>
          <div class="output-area">
            <div class="result-content" v-if="result">
              {{ result }}
            </div>
            <div v-else class="placeholder">
              <div class="ai-thinking">
                <div class="brain-icon">🧠</div>
                <p>AI正在思考...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 引擎状态显示在左下角 -->
      <div class="engine-status" :class="translationStatus">
        <div class="status-indicator">
          <div class="indicator-light"></div>
        </div>
        <span class="engine-text">{{ statusText }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';

// 防抖函数
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export default {
  name: 'ApiTranslation',
  setup() {
    const sourceText = ref('');
    const targetLang = ref('zh');
    const provider = ref('llama-cpp');
    const result = ref('');
    const translationStatus = ref('idle'); // idle, translating, completed
    
    // 模型选择
    const models = ref([]);
    const selectedModel = ref('');
    const loadingModels = ref(false);
    
    // API服务商选择（云端API时使用）
    const apiProvider = ref('baidu');
    
    const targetLangMap = {
      'zh': '中文',
      'en': '英语',
      'ja': '日语',
      'ko': '韩语',
      'fr': '法语',
      'de': '德语',
      'es': '西班牙语',
      'ru': '俄语',
      'ar': '阿拉伯语'
    };
    
    // 计算状态文本
    const statusText = computed(() => {
      switch (translationStatus.value) {
        case 'translating':
          return '翻译中';
        case 'completed':
          return '已完成';
        default:
          return '已就绪';
      }
    });
    
    // 加载模型列表
    const loadModels = async () => {
      if (provider.value !== 'llama-cpp') {
        models.value = [];
        selectedModel.value = '';
        return;
      }
      
      loadingModels.value = true;
      try {
        const response = await fetch('http://127.0.0.1:8000/models');
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            models.value = data.models || [];
            // 如果有模型，加载当前配置中的模型
            if (models.value.length > 0) {
              await loadConfig();
            }
          }
        }
      } catch (error) {
        console.error('加载模型列表失败:', error);
        models.value = [];
      } finally {
        loadingModels.value = false;
      }
    };
    
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
              // 设置当前选中的模型
              if (data.config.current_model && models.value.length > 0) {
                selectedModel.value = data.config.current_model;
              } else if (models.value.length > 0 && !selectedModel.value) {
                // 如果没有当前模型，选择第一个
                selectedModel.value = models.value[0].name;
                await switchModel();
              }
              return; // 成功连接，退出
            }
          }
        } catch (error) {
          // 连接失败，继续重试
          if (i < retries - 1) {
            await new Promise(resolve => setTimeout(resolve, delay));
            continue;
          }
          // 最后一次尝试失败
          if (import.meta.env.DEV && error.name !== 'AbortError') {
            console.warn('无法连接到后端服务器，使用默认配置');
          }
        }
      }
    };
    
    // 切换模型
    const switchModel = async () => {
      if (!selectedModel.value || provider.value !== 'llama-cpp') return;
      
      try {
        const response = await fetch('http://127.0.0.1:8000/switch-model', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model_name: selectedModel.value
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            console.log('模型切换成功:', data.message);
            // 如果正在翻译，重新翻译
            if (sourceText.value.trim()) {
              await translate();
            }
          }
        } else {
          console.error('切换模型失败');
        }
      } catch (error) {
        console.error('切换模型失败:', error);
      }
    };
    
    // 百度翻译
    const translateWithBaidu = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/translate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: sourceText.value,
            source_lang: 'auto',
            target_lang: targetLang.value,
            provider: 'baidu'
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          result.value = data.translated_text;
          translationStatus.value = 'completed';
          // 3秒后自动切换回就绪状态
          setTimeout(() => {
            if (translationStatus.value === 'completed') {
              translationStatus.value = 'idle';
            }
          }, 3000);
        } else {
          result.value = `翻译失败: ${data.error}`;
          translationStatus.value = 'idle';
        }
      } catch (error) {
        console.error('翻译错误:', error);
        result.value = `翻译失败: ${error.message}`;
        translationStatus.value = 'idle';
      }
    };
    
    // API服务商切换处理
    const onApiProviderChange = () => {
      // 更新实际的provider为百度
      provider.value = 'baidu';
      // 如果已有文本，重新翻译
      if (sourceText.value.trim()) {
        translate();
      }
    };
    
    // 翻译引擎切换处理
    const onProviderChange = async () => {
      if (provider.value === 'llama-cpp') {
        await loadModels();
      } else {
        models.value = [];
        selectedModel.value = '';
        // 切换到云端API时，默认使用百度
        if (provider.value === 'openai' || provider.value === 'baidu') {
          apiProvider.value = 'baidu';
          provider.value = 'baidu';
        }
      }
      // 如果已有文本，重新翻译
      if (sourceText.value.trim()) {
        await translate();
      }
    };
    
    onMounted(async () => {
      await loadConfig();
      if (provider.value === 'llama-cpp') {
        await loadModels();
      }
    });
    
    // 使用SSE进行流式翻译
    const translate = async () => {
      if (!sourceText.value.trim()) {
        result.value = '';
        translationStatus.value = 'idle';
        return;
      }
      
      // 如果使用本地模型，检查是否已选择模型
      if (provider.value === 'llama-cpp' && !selectedModel.value) {
        result.value = '请先选择模型';
        translationStatus.value = 'idle';
        return;
      }
      
      // 如果使用百度翻译，使用普通API
      if (provider.value === 'baidu') {
        translationStatus.value = 'translating';
        await translateWithBaidu();
        return;
      }
      
      // 开始翻译
      translationStatus.value = 'translating';
      
      try {
        // 使用流式API进行翻译（仅本地模型）
        const apiUrl = 'http://127.0.0.1:8000/translate-stream';
          
        if (provider.value === 'llama-cpp') {
          // 使用流式API
          const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              text: sourceText.value,
              source_lang: 'auto',
              target_lang: targetLang.value,
              provider: provider.value
            })
          });
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
          }
          
          // 使用流式响应
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          
          result.value = '';
          
          while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // 按行分割并处理每个事件
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  
                  if (data.error) {
                    throw new Error(data.error);
                  }
                  
                  if (data.text) {
                    result.value += data.text;
                    await new Promise(resolve => setTimeout(resolve, 0));
                  }
                  
                  if (data.done) {
                    translationStatus.value = 'completed';
                    // 3秒后自动切换回就绪状态
                    setTimeout(() => {
                      if (translationStatus.value === 'completed') {
                        translationStatus.value = 'idle';
                      }
                    }, 3000);
                    return;
                  }
                } catch (e) {
                  console.error('解析流数据时出错:', e);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('翻译错误:', error);
        result.value = `翻译失败: ${error.message}`;
        translationStatus.value = 'idle';
      }
    };
    
    // 清空输入
    const clearInput = () => {
      sourceText.value = '';
      result.value = '';
      translationStatus.value = 'idle';
    };
    
    // 复制原文
    const copyInput = () => {
      if (sourceText.value) {
        navigator.clipboard.writeText(sourceText.value);
        showNotification('原文已复制到剪贴板');
      }
    };
    
    // 复制译文
    const copyResult = () => {
      if (result.value) {
        navigator.clipboard.writeText(result.value);
        showNotification('译文已复制到剪贴板');
      }
    };
    
    // 朗读译文
    const speakResult = () => {
      if (result.value && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(result.value);
        utterance.rate = 0.8;
        utterance.pitch = 1;
        speechSynthesis.speak(utterance);
      } else {
        showNotification('浏览器不支持语音合成');
      }
    };
    
    // 显示通知
    const showNotification = (message) => {
      // 简单的通知实现
      console.log(message);
    };
    
    // 防抖函数
    const debouncedTranslate = debounce(translate, 500);
    
    return {
      sourceText,
      targetLang,
      provider,
      result,
      targetLangMap,
      translationStatus,
      statusText,
      models,
      selectedModel,
      loadingModels,
      apiProvider,
      debouncedTranslate,
      clearInput,
      copyInput,
      copyResult,
      speakResult,
      switchModel,
      onProviderChange,
      onApiProviderChange,
      translateWithBaidu
    };
  }
};
</script>

<style scoped>
.smart-translation {
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
}

.controls-section {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

/* 控制组基础样式 */
.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 0 0 auto;
}

.control-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.8rem;
  letter-spacing: 0.2px;
  margin-bottom: 2px;
}

.label-icon {
  font-size: 1rem;
  opacity: 0.8;
}

.label-text {
  font-weight: 600;
}

/* 目标语言选择器 - 最左边 */
.lang-selector {
  min-width: 160px;
}

/* 现代下拉框样式 */
.modern-select {
  padding: 12px 36px 12px 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 12px center;
  background-repeat: no-repeat;
  background-size: 16px;
  min-width: 160px;
  height: 52px;
  box-sizing: border-box;
}

[data-theme="dark"] .modern-select {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23cbd5e1' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
}

.modern-select:hover {
  border-color: var(--border-hover);
  background-color: var(--bg-primary);
}

.modern-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
  background-color: var(--bg-primary);
}

/* 翻译引擎选择器 - 卡片式设计 */
.engine-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 0 0 auto;
}

.engine-toggle-group {
  display: flex;
  gap: 8px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-color);
  height: 52px;
  box-sizing: border-box;
  align-items: center;
}

.engine-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  white-space: nowrap;
  height: 44px;
  box-sizing: border-box;
}

.engine-toggle-btn .btn-icon {
  font-size: 1.1rem;
  line-height: 1;
}

.engine-toggle-btn .btn-text {
  font-weight: 600;
}

.engine-toggle-btn .btn-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--primary-color);
  color: white;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
  line-height: 1.2;
}

.engine-toggle-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.engine-toggle-btn.active {
  background: var(--primary-color);
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.engine-toggle-btn.active .btn-icon {
  filter: brightness(1.2);
}

[data-theme="dark"] .engine-toggle-btn.active {
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.4);
}

/* 模型选择器 */
.model-selector {
  min-width: 240px;
  flex: 1 1 auto;
}

/* 服务商选择器 */
.provider-selector {
  min-width: 160px;
  flex: 0 0 auto;
}

.translation-workspace {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 12px;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.input-panel,
.output-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  flex: 1;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-color);
  padding: 16px;
  transition: var(--transition);
  overflow: hidden;
}


.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border-color);
}

.panel-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.1px;
}

.panel-actions {
  display: flex;
  gap: 10px;
}

.btn.small {
  padding: 6px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
}

.input-area,
.output-area {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.input-area textarea {
  width: 100%;
  flex: 1;
  min-height: 0;
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 1rem;
  resize: none;
  font-family: inherit;
  line-height: 1.7;
  transition: var(--transition);
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.input-area textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px var(--primary-light);
  background-color: var(--bg-primary);
}

.input-area textarea::placeholder {
  color: var(--text-tertiary);
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-size: 0.95rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 2px dashed var(--border-color);
  padding: 30px 16px;
  min-height: 0;
}

.ai-thinking {
  text-align: center;
}

.brain-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  animation: pulse 2s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(99, 102, 241, 0.2));
}

@keyframes pulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.15);
    opacity: 0.8;
  }
}

.ai-thinking p {
  color: var(--text-secondary);
  font-weight: 500;
  margin: 0;
}

.result-content {
  line-height: 1.7;
  color: var(--text-primary);
  font-size: 1rem;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 2px solid var(--border-color);
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* 引擎状态显示在左下角 - 指示灯样式 */
.engine-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 2px solid var(--border-color);
  font-size: 0.8rem;
  font-weight: 500;
  margin-top: auto;
  align-self: flex-start;
}

.status-indicator {
  position: relative;
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}

.indicator-light {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  transition: var(--transition);
  box-shadow: 0 0 8px currentColor;
}

/* 绿灯 - 已就绪 */
.engine-status.idle .indicator-light {
  background-color: var(--success-color);
  color: var(--success-color);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

/* 黄灯 - 翻译中 */
.engine-status.translating .indicator-light {
  background-color: var(--warning-color);
  color: var(--warning-color);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.6);
  animation: pulse-yellow 1.5s ease-in-out infinite;
}

@keyframes pulse-yellow {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* 绿灯 - 已完成 */
.engine-status.completed .indicator-light {
  background-color: var(--success-color);
  color: var(--success-color);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

.engine-text {
  color: var(--text-primary);
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .controls-section {
    gap: 16px;
  }
  
  .lang-selector,
  .model-selector {
    min-width: 140px;
  }
  
  .engine-toggle-group {
    flex-wrap: wrap;
  }
  
  .translation-workspace {
    gap: 20px;
  }
  
  .input-panel,
  .output-panel {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .translation-workspace {
    grid-template-columns: 1fr;
    gap: 20px;
    min-height: 0;
  }
  
  .controls-section {
    flex-direction: column;
    gap: 16px;
  }
  
  .lang-selector,
  .model-selector {
    width: 100%;
    min-width: 100%;
  }
  
  .engine-selector {
    width: 100%;
  }
  
  .engine-toggle-group {
    width: 100%;
    justify-content: stretch;
  }
  
  .engine-toggle-btn {
    flex: 1;
    justify-content: center;
  }
  
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
  
  .panel-actions {
    align-self: stretch;
    justify-content: space-between;
  }
  
  .input-area textarea,
  .placeholder,
  .result-content {
    min-height: 0;
  }
}

@media (max-width: 480px) {
  .smart-translation {
    gap: 20px;
  }
  
  .controls-section {
    gap: 12px;
  }
  
  .engine-toggle-btn {
    padding: 8px 12px;
    font-size: 0.8rem;
  }
  
  .engine-toggle-btn .btn-icon {
    font-size: 1rem;
  }
  
  .panel-actions {
    flex-wrap: wrap;
  }
  
  .btn.small {
    padding: 10px 14px;
    font-size: 0.8rem;
  }
  
  .input-panel,
  .output-panel {
    padding: 16px;
  }
  
  .engine-status {
    padding: 10px 14px;
    font-size: 0.85rem;
  }
}
</style>