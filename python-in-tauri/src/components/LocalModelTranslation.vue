<template>
  <div class="local-model-translation">
    <div class="card">
      <h2 class="card-title">
        <i class="icon">🤖</i> 本地模型翻译
      </h2>
      
      <div class="translation-controls">
        <div class="input-group">
          <label for="model-select">翻译模型</label>
          <select id="model-select" v-model="selectedModel" @change="switchModel" :disabled="loadingModels">
            <option value="" disabled>{{ loadingModels ? '加载中...' : (models.length === 0 ? '未找到模型' : '请选择模型') }}</option>
            <option v-for="model in models" :key="model.name" :value="model.name">
              {{ model.name }} ({{ model.size_mb }} MB)
            </option>
          </select>
        </div>
        
        <div class="input-group">
          <label for="local-target-lang">目标语言</label>
          <select id="local-target-lang" v-model="targetLang" @change="debouncedTranslate">
            <option value="zh">中文</option>
            <option value="en">英语</option>
            <option value="ja">日语</option>
            <option value="ko">韩语</option>
            <option value="fr">法语</option>
            <option value="de">德语</option>
            <option value="es">西班牙语</option>
          </select>
        </div>
        
        <div class="core-control">
          <label for="thread-count">核心数量</label>
          <select id="thread-count" v-model="threadCount" @change="updateThreadCount">
            <option v-for="n in availableCores" :key="n" :value="n">{{ n }} 核心</option>
          </select>
        </div>
      </div>
      
      <div class="translation-layout">
        <div class="input-section">
          <div class="input-group">
            <label for="local-source-text">原文</label>
            <textarea 
              id="local-source-text" 
              v-model="sourceText" 
              placeholder="请输入要翻译的文本..."
              @input="debouncedTranslate"
            ></textarea>
          </div>
        </div>
        
        <div class="output-section">
          <div class="input-group">
            <label>译文</label>
            <div class="translation-output">
              <div class="result-content">
                {{ result }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { debounce } from 'lodash-es';

export default {
  name: 'LocalModelTranslation',
  setup() {
    const sourceText = ref('');
    const targetLang = ref('zh');
    
    const result = ref('');
    
    // 模型选择
    const models = ref([]);
    const selectedModel = ref('');
    const loadingModels = ref(false);
    
    // CPU核心数控制
    const threadCount = ref(4);
    const availableCores = ref([1, 2, 4, 6, 8, 12, 16]); // 常见的核心数选项
    
    // 加载模型列表
    const loadModels = async () => {
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
    
    // 加载配置
    const loadConfig = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/config');
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            threadCount.value = data.config.threads || 4;
            // 设置当前选中的模型
            if (data.config.current_model) {
              selectedModel.value = data.config.current_model;
            } else if (models.value.length > 0) {
              // 如果没有当前模型，选择第一个
              selectedModel.value = models.value[0].name;
              await switchModel();
            }
          }
        }
      } catch (error) {
        console.error('加载配置失败:', error);
        // 如果加载失败，使用默认值
        threadCount.value = 4;
      }
    };
    
    // 切换模型
    const switchModel = async () => {
      if (!selectedModel.value) return;
      
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
    
    // 更新线程数配置
    const updateThreadCount = async () => {
      try {
        // 获取当前配置
        const response = await fetch('http://127.0.0.1:8000/config');
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            // 更新线程数并保存配置
            const updatedConfig = {
              ...data.config,
              threads: threadCount.value
            };
            
            const saveResponse = await fetch('http://127.0.0.1:8000/config', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(updatedConfig)
            });
            
            if (!saveResponse.ok) {
              console.error('保存线程数配置失败');
            }
          }
        }
      } catch (error) {
        console.error('更新线程数配置失败:', error);
      }
    };
    
    onMounted(async () => {
      // 先加载模型列表
      await loadModels();
      
      // 尝试检测实际CPU核心数
      detectActualCores();
    });
    
    // 检测实际CPU核心数
    const detectActualCores = () => {
      try {
        // 这里我们使用navigator.hardwareConcurrency来检测可用的核心数
        if (navigator.hardwareConcurrency) {
          const actualCores = navigator.hardwareConcurrency;
          // 生成核心数选项列表，最多不超过实际核心数
          const coresOptions = [];
          for (let i = 1; i <= Math.min(actualCores, 16); i *= 2) {
            coresOptions.push(i);
            if (i === 8 && i * 1.5 <= actualCores) {
              coresOptions.push(Math.floor(i * 1.5)); // 如12核
            }
          }
          if (actualCores > 16) {
            coresOptions.push(actualCores);
          }
          availableCores.value = [...new Set(coresOptions)].sort((a, b) => a - b);
        }
      } catch (error) {
        console.warn('无法检测CPU核心数，使用默认选项');
      }
    };
    
    // 使用SSE进行流式翻译
    const translate = async () => {
      if (!sourceText.value.trim()) {
        result.value = '';
        return;
      }
      
      if (!selectedModel.value) {
        result.value = '请先选择模型';
        return;
      }
      
      try {
        // 使用流式API进行翻译
        const response = await fetch('http://127.0.0.1:8000/translate-stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: sourceText.value,
            source_lang: 'auto', // 固定为auto，因为模型会自动识别
            target_lang: targetLang.value,
            provider: 'llama-cpp'
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
        
        result.value = ''; // 清空之前的结果
        
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          // 按行分割并处理每个事件
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 保留未完成的行
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)); // 移除 'data: ' 前缀
                
                if (data.error) {
                  throw new Error(data.error);
                }
                
                if (data.text) {
                  result.value += data.text; // 实时追加文本
                  
                  // 强制浏览器更新UI
                  await new Promise(resolve => setTimeout(resolve, 0));
                }
                
                if (data.done) {
                  // 翻译完成
                  return;
                }
              } catch (e) {
                console.error('解析流数据时出错:', e);
              }
            }
          }
        }
      } catch (error) {
        console.error('翻译错误:', error);
        result.value = `翻译失败: ${error.message}`;
      }
    };
    
    // 防抖函数，避免频繁调用翻译API
    const debouncedTranslate = debounce(translate, 500);
    
    return {
      sourceText,
      targetLang,
      result,
      models,
      selectedModel,
      loadingModels,
      threadCount,
      availableCores,
      debouncedTranslate,
      updateThreadCount,
      switchModel
    };
  }
};
</script>

<style scoped>
.local-model-translation {
  display: flex;
  flex-direction: column;
  gap: 28px;
  height: 100%;
}

.translation-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

.core-control {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.core-control label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.95rem;
  letter-spacing: 0.2px;
}

.core-control select {
  padding: 14px 18px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 1rem;
  cursor: pointer;
  transition: var(--transition);
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 14px center;
  background-repeat: no-repeat;
  background-size: 18px;
  padding-right: 44px;
}

[data-theme="dark"] .core-control select {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23cbd5e1' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
}

.core-control select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px var(--primary-light);
}

.translation-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  margin-bottom: 28px;
  flex: 1;
  min-height: 450px;
}

.input-section, 
.output-section {
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-color);
  padding: 24px;
  transition: var(--transition);
}

.input-section:hover,
.output-section:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
}

.translation-output {
  min-height: 350px;
  padding: 18px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
  font-family: inherit;
  white-space: pre-wrap;
  word-break: break-word;
  transition: var(--transition);
}

.translation-output:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px var(--primary-light);
}

.result-content {
  color: var(--text-primary);
  font-size: 1.05rem;
  line-height: 1.8;
  min-height: 300px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

.input-group label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.95rem;
  letter-spacing: 0.2px;
}

.input-group textarea {
  flex: 1;
  min-height: 350px;
  resize: vertical;
  padding: 18px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 1.05rem;
  font-family: inherit;
  line-height: 1.8;
  transition: var(--transition);
}

.input-group textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px var(--primary-light);
  background-color: var(--bg-primary);
}

.input-group textarea::placeholder {
  color: var(--text-tertiary);
}

.input-group select {
  padding: 14px 18px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 1rem;
  cursor: pointer;
  transition: var(--transition);
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 14px center;
  background-repeat: no-repeat;
  background-size: 18px;
  padding-right: 44px;
}

[data-theme="dark"] .input-group select {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23cbd5e1' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
}

.input-group select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px var(--primary-light);
}

@media (max-width: 1024px) {
  .translation-layout {
    gap: 20px;
  }
  
  .input-section,
  .output-section {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .translation-controls {
    grid-template-columns: 1fr;
  }
  
  .translation-layout {
    grid-template-columns: 1fr;
    gap: 20px;
    min-height: auto;
  }
  
  .input-group textarea,
  .translation-output {
    min-height: 250px;
  }
}

@media (max-width: 480px) {
  .local-model-translation {
    gap: 20px;
  }
  
  .input-section,
  .output-section {
    padding: 16px;
  }
  
  .input-group textarea,
  .translation-output {
    min-height: 200px;
    padding: 14px;
  }
}
</style>