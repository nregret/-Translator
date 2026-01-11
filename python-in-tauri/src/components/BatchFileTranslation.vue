<template>
  <div class="batch-file-translation">
    <div class="card" :class="{ 'translating': isTranslating || translationProgress.total > 0 }" :style="progressBorderStyle">
      <h2 class="card-title">
        <i class="icon">📁</i> 批量文件翻译
      </h2>
      
      <div class="controls-section">
        <!-- 目标语言 - 最左边 -->
        <div class="control-group lang-selector">
          <label for="batch-target-lang" class="control-label">
            <span class="label-icon">🌐</span>
            <span class="label-text">目标语言</span>
          </label>
          <select id="batch-target-lang" v-model="targetLang" class="modern-select">
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
        
        <!-- 翻译引擎切换 -->
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
          <label for="batch-model-select" class="control-label">
            <span class="label-icon">🤖</span>
            <span class="label-text">翻译模型</span>
          </label>
          <select 
            id="batch-model-select" 
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
          <label for="batch-provider-select" class="control-label">
            <span class="label-icon">🔌</span>
            <span class="label-text">服务商</span>
          </label>
          <select 
            id="batch-provider-select" 
            v-model="apiProvider" 
            @change="onApiProviderChange"
            class="modern-select"
          >
            <option value="baidu">百度翻译</option>
          </select>
        </div>
      </div>
      
      <!-- 文件上传区域 -->
      <div class="file-upload-section">
        <div class="file-list-container">
          <div class="upload-buttons">
            <button @click="selectFiles" class="upload-btn file-btn">
              <span class="btn-icon">📄</span>
              <span class="btn-text">选择文件</span>
            </button>
            <button @click="selectFolder" class="upload-btn folder-btn">
              <span class="btn-icon">📁</span>
              <span class="btn-text">选择文件夹</span>
            </button>
          </div>
          
          <div v-if="selectedFiles.length > 0" class="file-list-content">
            <div class="file-list-header">
              <span class="file-count-text">已选择 {{ selectedFiles.length }} 个文件</span>
              <button @click="clearFiles" class="clear-btn">清空</button>
            </div>
            <div class="file-list">
              <div class="file-item" v-for="(file, index) in selectedFiles" :key="index">
                <span class="file-name">{{ file }}</span>
                <button @click.stop="removeFile(index)" class="remove-btn">×</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 保存选项 -->
      <div class="save-options">
        <div class="option-group">
          <label class="radio-option">
            <input 
              type="radio" 
              v-model="saveMode" 
              value="replace"
            />
            <span>替换原文件</span>
          </label>
          <label class="radio-option">
            <input 
              type="radio" 
              v-model="saveMode" 
              value="save_as"
            />
            <span>另存为</span>
          </label>
        </div>
        
        <div class="save-path-selector" :class="{ disabled: saveMode === 'replace' }">
          <label class="path-label">保存路径：</label>
          <div class="path-display">{{ savePath || '未选择' }}</div>
          <button 
            @click="selectSavePath" 
            class="btn btn-secondary small"
            :disabled="saveMode === 'replace'"
          >
            <span>📂</span> 选择文件夹
          </button>
        </div>
      </div>
      
      <!-- 翻译按钮 -->
      <div class="translate-action">
        <button 
          @click="startBatchTranslation" 
          class="btn btn-primary"
          :disabled="selectedFiles.length === 0 || isTranslating || (provider === 'llama-cpp' && !selectedModel) || (saveMode === 'save_as' && !savePath)"
        >
          <span v-if="!isTranslating">🚀</span>
          <span v-else class="spinner">⏳</span>
          {{ isTranslating ? '翻译中...' : '开始翻译' }}
        </button>
      </div>
      
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';

export default {
  name: 'BatchFileTranslation',
  setup() {
    const targetLang = ref('zh');
    const provider = ref('llama-cpp');
    const result = ref('');
    
    // 模型选择
    const models = ref([]);
    const selectedModel = ref('');
    const loadingModels = ref(false);
    
    // API服务商选择（云端API时使用）
    const apiProvider = ref('baidu');
    
    // 文件选择
    const selectedFiles = ref([]);
    const saveMode = ref('replace'); // replace or save_as
    const savePath = ref('');
    
    // 翻译状态
    const isTranslating = ref(false);
    const translationProgress = ref({
      current: 0,
      total: 0,
      percent: 0
    });
    
    // 计算状态文本
    // 计算进度条边框样式
    const progressBorderStyle = computed(() => {
      if (translationProgress.value.total > 0) {
        const percent = translationProgress.value.percent;
        return {
          '--progress-percent': `${percent}%`
        };
      }
      return {};
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
    
    // 加载配置
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
          }
        } else {
          console.error('切换模型失败');
        }
      } catch (error) {
        console.error('切换模型失败:', error);
      }
    };
    
    // API服务商切换处理
    const onApiProviderChange = () => {
      // 更新实际的provider为百度
      provider.value = 'baidu';
    };
    
    // 翻译引擎切换处理
    const onProviderChange = async () => {
      if (provider.value === 'llama-cpp') {
        await loadModels();
      } else {
        models.value = [];
        selectedModel.value = '';
        // 切换到云端API时，默认使用百度
        if (provider.value === 'openai') {
          apiProvider.value = 'baidu';
          provider.value = 'baidu';
        }
      }
    };
    
    // 选择文件
    const selectFiles = async () => {
      try {
        // 动态导入Tauri对话框插件
        const { open } = await import('@tauri-apps/plugin-dialog');
        
        // 打开文件选择对话框
        const result = await open({
          multiple: true,
          filters: [{ name: 'Text Files', extensions: ['txt'] }]
        });
        
        if (result) {
          let paths = [];
          
          if (Array.isArray(result)) {
            paths = result.map(f => typeof f === 'string' ? f : f.path || f.name);
          } else {
            const path = typeof result === 'string' ? result : result.path || result.name;
            if (path) {
              paths = [path];
            }
          }
          
          // 过滤只保留 .txt 文件并添加到列表
          for (const path of paths) {
            if (path.toLowerCase().endsWith('.txt')) {
              if (!selectedFiles.value.includes(path)) {
                selectedFiles.value.push(path);
              }
            }
          }
        }
      } catch (error) {
        console.error('选择文件失败:', error);
        alert('选择文件失败: ' + error.message);
      }
    };
    
    // 选择文件夹
    const selectFolder = async () => {
      try {
        // 动态导入Tauri对话框插件
        const { open } = await import('@tauri-apps/plugin-dialog');
        
        // 打开文件夹选择对话框
        const folderResult = await open({
          directory: true,
          multiple: false
        });
        
        if (folderResult) {
          const folderPath = typeof folderResult === 'string' ? folderResult : folderResult.path || folderResult.name;
          if (folderPath) {
            // 扫描文件夹中的所有txt文件
            try {
              const files = await invoke('scan_folder_txt_files', { folderPath });
              if (files && Array.isArray(files) && files.length > 0) {
                selectedFiles.value = [...new Set([...selectedFiles.value, ...files])];
              } else {
                alert('该文件夹中没有找到 .txt 文件');
              }
            } catch (error) {
              console.error('扫描文件夹失败:', error);
              alert(`扫描文件夹失败: ${error.message}`);
            }
          }
        }
      } catch (error) {
        console.error('选择文件夹失败:', error);
        alert('选择文件夹失败: ' + error.message);
      }
    };
    
    // 选择保存路径
    const selectSavePath = async () => {
      try {
        // 动态导入Tauri对话框插件
        const { open } = await import('@tauri-apps/plugin-dialog');
        
        const result = await open({
          directory: true,
          multiple: false
        });
        
        if (result) {
          const path = typeof result === 'string' ? result : result.path || result.name;
          if (path) {
            savePath.value = path;
          }
        }
      } catch (error) {
        console.error('选择保存路径失败:', error);
      }
    };
    
    // 移除文件
    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1);
    };
    
    // 清空文件
    const clearFiles = () => {
      selectedFiles.value = [];
    };
    
    // 开始批量翻译
    const startBatchTranslation = async () => {
      if (selectedFiles.value.length === 0) return;
      if (provider.value === 'llama-cpp' && !selectedModel.value) {
        alert('请先选择模型');
        return;
      }
      if (saveMode.value === 'save_as' && !savePath.value) {
        alert('请选择保存路径');
        return;
      }
      
      isTranslating.value = true;
      const totalFiles = selectedFiles.value.length;
      let successCount = 0;
      let failCount = 0;
      
      // 初始化进度
      translationProgress.value = {
        current: 0,
        total: totalFiles,
        percent: 0
      };
      
      try {
        // 逐个文件翻译，以便实时更新进度
        for (let i = 0; i < selectedFiles.value.length; i++) {
          const filePath = selectedFiles.value[i];
          
          try {
            // 读取文件内容
            const fileContent = await invoke('read_file_content', { filePath });
            
            if (!fileContent || !fileContent.trim()) {
              failCount++;
              continue;
            }
            
            // 调用翻译API
            const translateResponse = await fetch('http://127.0.0.1:8000/translate', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                text: fileContent,
                source_lang: 'auto',
                target_lang: targetLang.value,
                provider: provider.value === 'llama-cpp' ? 'llama-cpp' : 'baidu'
              })
            });
            
            if (!translateResponse.ok) {
              const errorData = await translateResponse.json().catch(() => ({}));
              throw new Error(errorData.detail || `翻译失败: ${translateResponse.status}`);
            }
            
            const translateData = await translateResponse.json();
            
            if (translateData.success) {
              // 保存翻译后的文件
              let finalSavePath;
              if (saveMode.value === 'replace') {
                finalSavePath = filePath;
              } else {
                // 另存为模式
                const fileName = filePath.split(/[/\\]/).pop();
                const name = fileName.replace(/\.txt$/, '');
                const newFileName = `${name}_translated.txt`;
                finalSavePath = await invoke('join_path', { 
                  dir: savePath.value, 
                  file: newFileName 
                });
              }
              
              await invoke('write_file_content', { 
                filePath: finalSavePath, 
                content: translateData.translated_text 
              });
              
              successCount++;
            } else {
              failCount++;
            }
          } catch (error) {
            console.error(`翻译文件 ${filePath} 失败:`, error);
            failCount++;
          }
          
          // 实时更新进度
          translationProgress.value = {
            current: i + 1,
            total: totalFiles,
            percent: Math.round(((i + 1) / totalFiles) * 100)
          };
        }
        
        // 翻译完成，等待3秒后重置
        setTimeout(() => {
          translationProgress.value = {
            current: 0,
            total: 0,
            percent: 0
          };
        }, 3000);
        
        alert(`翻译完成！成功: ${successCount}，失败: ${failCount}`);
      } catch (error) {
        console.error('批量翻译错误:', error);
        alert(`翻译失败: ${error.message}`);
      } finally {
        isTranslating.value = false;
      }
    };
    
    onMounted(async () => {
      await loadConfig();
      if (provider.value === 'llama-cpp') {
        await loadModels();
      }
    });
    
    return {
      targetLang,
      provider,
      models,
      selectedModel,
      loadingModels,
      apiProvider,
      selectedFiles,
      saveMode,
      savePath,
      isTranslating,
      translationProgress,
      progressBorderStyle,
      loadModels,
      switchModel,
      onProviderChange,
      onApiProviderChange,
      selectFiles,
      selectFolder,
      selectSavePath,
      removeFile,
      clearFiles,
      startBatchTranslation
    };
  }
};
</script>

<style scoped>
.batch-file-translation {
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
  overflow: hidden;
  position: relative;
  border-bottom: 4px solid var(--border-color);
}

.card.translating::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  width: var(--progress-percent, 0%);
  background: var(--primary-color);
  transition: width 0.3s ease;
  z-index: 1;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.controls-section {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

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

.lang-selector {
  min-width: 160px;
}

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

.model-selector {
  min-width: 240px;
  flex: 1 1 auto;
}

.provider-selector {
  min-width: 160px;
  flex: 0 0 auto;
}

.file-upload-section {
  margin-bottom: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.upload-buttons {
  display: flex;
  gap: 12px;  /* 减少间距 */
  margin-bottom: 12px;  /* 减少下边距 */
}

.upload-btn {
  flex: 1;
  display: flex;
  flex-direction: row;  /* 改为水平布局 */
  align-items: center;
  justify-content: center;
  gap: 8px;  /* 图标和文字之间的间距 */
  padding: 12px 16px;  /* 大幅减少内边距 */
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  min-height: 48px;  /* 设置最小高度 */
}

.upload-btn:hover {
  border-color: var(--primary-color);
  background: var(--bg-tertiary);
  transform: translateY(-1px);  /* 减少悬浮效果 */
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.upload-btn .btn-icon {
  font-size: 1.2rem;  /* 大幅缩小图标 */
  opacity: 0.8;
}

.upload-btn .btn-text {
  font-size: 0.85rem;  /* 稍微缩小文字 */
  font-weight: 500;
  color: var(--text-primary);
}

.file-list-container {
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.file-list-content {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.file-count-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.file-name {
  font-size: 0.85rem;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 8px;
  line-height: 1;
  transition: color 0.2s ease;
}

.remove-btn:hover {
  color: var(--error-color);
}

.file-count {
  font-size: 0.85rem;
  color: var(--text-secondary);
  text-align: center;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.clear-btn {
  background: var(--error-color) !important;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 6px 16px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background: #dc2626 !important;
  transform: scale(1.05);
}

.save-options {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 2px solid var(--border-color);
  flex-shrink: 0;
}

.option-group {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.radio-option input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--primary-color);
}

.save-path-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  transition: opacity 0.2s ease;
}

.save-path-selector.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.save-path-selector.disabled .path-display {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.save-path-selector.disabled .btn {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-path-selector.disabled .path-label {
  color: var(--text-secondary);
}

.path-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.path-display {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.translate-action {
  margin-bottom: 20px;
  flex-shrink: 0;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 2px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-primary);
  border-color: var(--border-hover);
}

.btn.small {
  padding: 8px 16px;
  font-size: 0.8rem;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}


.engine-text {
  font-weight: 600;
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .controls-section {
    flex-direction: column;
    gap: 16px;
  }
  
  .lang-selector,
  .model-selector,
  .provider-selector {
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
}
</style>
