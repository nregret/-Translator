use std::process::{Command, Child};
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::Manager;
use std::fs;

static PYTHON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn scan_folder_txt_files(folder_path: String) -> Result<Vec<String>, String> {
    let path = PathBuf::from(folder_path);
    if !path.exists() || !path.is_dir() {
        return Err("文件夹不存在".to_string());
    }
    
    let mut txt_files = Vec::new();
    
    fn scan_dir(dir: &PathBuf, files: &mut Vec<String>) {
        if let Ok(entries) = fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    scan_dir(&path, files);
                } else if path.extension().and_then(|s| s.to_str()) == Some("txt") {
                    if let Some(path_str) = path.to_str() {
                        files.push(path_str.to_string());
                    }
                }
            }
        }
    }
    
    scan_dir(&path, &mut txt_files);
    Ok(txt_files)
}

#[tauri::command]
fn check_path_type(path: String) -> Result<serde_json::Value, String> {
    use serde_json::json;
    let path_buf = PathBuf::from(&path);
    
    if !path_buf.exists() {
        return Err("路径不存在".to_string());
    }
    
    let is_file = path_buf.is_file();
    let is_directory = path_buf.is_dir();
    
    Ok(json!({
        "isFile": is_file,
        "isDirectory": is_directory,
        "path": path
    }))
}

#[tauri::command]
fn read_file_content(file_path: String) -> Result<String, String> {
    match fs::read_to_string(&file_path) {
        Ok(content) => Ok(content),
        Err(e) => Err(format!("读取文件失败: {}", e))
    }
}

#[tauri::command]
fn write_file_content(file_path: String, content: String) -> Result<(), String> {
    // 确保目录存在
    if let Some(parent) = PathBuf::from(&file_path).parent() {
        if let Err(e) = fs::create_dir_all(parent) {
            return Err(format!("创建目录失败: {}", e));
        }
    }
    
    match fs::write(&file_path, content) {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("写入文件失败: {}", e))
    }
}

#[tauri::command]
fn join_path(dir: String, file: String) -> Result<String, String> {
    let path = PathBuf::from(dir).join(file);
    path.to_str()
        .map(|s| s.to_string())
        .ok_or_else(|| "路径转换失败".to_string())
}

/// 检查资源目录是否有效（包含 python 和 backend 子目录）
fn is_valid_resource_dir(path: &PathBuf) -> bool {
    path.exists() && 
    path.join("python").exists() && 
    path.join("backend").exists()
}

fn get_resource_dir(app: &tauri::AppHandle) -> PathBuf {
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let resources_path = exe_dir.join("resources");
            if is_valid_resource_dir(&resources_path) {
                return resources_path;
            }
        }
    }
    
    if let Ok(resource_path) = app.path().resource_dir() {
        if is_valid_resource_dir(&resource_path) {
            return resource_path;
        }
    }
    
    if let Ok(current_dir) = std::env::current_dir() {
        let mut search_dir = current_dir.clone();
        loop {
            let src_tauri_dir = search_dir.join("src-tauri");
            if src_tauri_dir.exists() && src_tauri_dir.is_dir() {
                let resources_path = search_dir.join("resources");
                if is_valid_resource_dir(&resources_path) {
                    return resources_path;
                }
                return resources_path;
            }
            
            if let Some(parent) = search_dir.parent() {
                search_dir = parent.to_path_buf();
            } else {
                break;
            }
        }
    }
    
    if let Ok(current_dir) = std::env::current_dir() {
        let resources_path = current_dir.join("resources");
        if is_valid_resource_dir(&resources_path) {
            return resources_path;
        }
    }
    
    app.path().resource_dir().expect("无法找到资源目录")
}

fn start_python_server(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let resource_dir = get_resource_dir(app);

    let python_exe = if cfg!(windows) {
        resource_dir.join("python").join("python.exe")
    } else {
        resource_dir.join("python").join("python3")
    };

    let backend_main = resource_dir.join("backend").join("main.py");
    let backend_dir = resource_dir.join("backend");

    if !python_exe.exists() || !backend_main.exists() || !backend_dir.exists() {
        return Err("Python环境或后端文件不完整".into());
    }

    let child_result = Command::new(&python_exe)
        .arg(&backend_main)
        .current_dir(&backend_dir)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn();

    match child_result {
        Ok(child) => {
            let mut process_guard = PYTHON_PROCESS.lock().unwrap();
            *process_guard = Some(child);
            drop(process_guard);
            Ok(())
        }
        Err(e) => {
            Err(format!("无法启动Python进程: {}", e).into())
        }
    }
}
fn wait_for_server(max_retries: u32) -> bool {
    use std::time::Duration;
    use std::thread;
    
    for i in 0..max_retries {
        thread::sleep(Duration::from_millis(500));
        
        match reqwest::blocking::get("http://127.0.0.1:8000/config") {
            Ok(response) => {
                if response.status().is_success() {
                    return true;
                }
            }
            Err(_) => {}
        }
        
        if i < max_retries - 1 {
            println!("等待后端服务器启动... (尝试 {}/{})", i + 1, max_retries);
        }
    }
    
    false
}

/// 停止 Python 后端服务器
fn stop_python_server() {
    let mut process_guard = PYTHON_PROCESS.lock().unwrap();
    if let Some(mut child) = process_guard.take() {
        println!("正在停止 Python 后端服务器...");
        
        #[cfg(windows)]
        {
            // Windows 上先尝试正常终止
            let pid = child.id();
            let _ = child.kill();
            
            // 等待一小段时间看进程是否结束
            std::thread::sleep(std::time::Duration::from_millis(100));
            
            // 如果进程还在运行，使用 taskkill 强制终止进程树
            if child.try_wait().is_ok() {
                // 进程已结束
            } else {
                // 使用 taskkill 强制终止进程树
                use std::process::Stdio;
                let _ = Command::new("taskkill")
                    .args(&["/F", "/T", "/PID", &pid.to_string()])
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .output();
            }
        }
        
        #[cfg(not(windows))]
        {
            // Unix 系统上发送 SIGTERM
            let _ = child.kill();
        }
        
        let _ = child.wait();
        println!("Python 后端服务器已停止");
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![greet, scan_folder_txt_files, check_path_type, read_file_content, write_file_content, join_path])
        .setup(|app| {
            match start_python_server(app.handle()) {
                Ok(_) => {
                    if !wait_for_server(20) {
                        println!("警告: 后端服务器启动超时");
                    }
                }
                Err(e) => {
                    println!("启动失败: {}", e);
                }
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            // 当窗口关闭时检查是否还有窗口
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                // 延迟检查，因为窗口可能还未完全关闭
                let app_handle = window.app_handle().clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_millis(100));
                    // 检查是否还有窗口
                    let windows = app_handle.webview_windows();
                    if windows.is_empty() {
                        stop_python_server();
                    }
                });
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
    
    // 确保应用退出时清理
    stop_python_server();
}
