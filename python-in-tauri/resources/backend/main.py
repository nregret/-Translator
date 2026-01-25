import sys
import os
from pathlib import Path

def main():
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    sys.path.insert(0, str(backend_dir))
    sys.path.insert(0, str(project_root))

    try:
        from translation_api import app
        import uvicorn
        import socket

        def find_available_port(start_port=8000, max_attempts=20):
            for port in range(start_port, start_port + max_attempts):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.bind(('127.0.0.1', port))
                        return port
                except OSError:
                    continue
            return None

        port = find_available_port(8000)
        if port is None:
            return

        try:
            port_config_path = project_root / "port_config.json"
            import json
            with open(port_config_path, 'w', encoding='utf-8') as f:
                json.dump({"port": port}, f)
        except:
            pass

        uvicorn.run(
            "translation_api:app",
            host="127.0.0.1",
            port=port,
            reload=False,
            log_level="error",
            access_log=False
        )

    except Exception:
        pass

if __name__ == "__main__":
    main()