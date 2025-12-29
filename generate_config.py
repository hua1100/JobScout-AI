import os
import sys
import json
import shutil

def get_python_path():
    # 取得當前虛擬環境的 python 路徑
    return sys.executable

def main():
    python_path = get_python_path()
    script_path = os.path.abspath("scraper_mcp.py")
    
    config = {
        "mcpServers": {
            "104-jobs": {
                "command": "uv",
                "args": [
                    "--directory",
                    os.getcwd(),
                    "run",
                    "scraper_mcp.py"
                ]
            }
        }
    }
    
    print("\n請將以下設定複製到您的 Claude Desktop 設定檔中:\n")
    print(json.dumps(config, indent=2))
    print("\n設定檔路徑 (Mac): ~/Library/Application Support/Claude/claude_desktop_config.json")
    
    # 嘗試讀取現有設定
    config_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    if os.path.exists(config_path):
        print(f"\n檢測到您的設定檔已存在: {config_path}")
        try:
            with open(config_path, 'r') as f:
                current_config = json.load(f)
            print("目前的設定內容中包含 keys:", list(current_config.get("mcpServers", {}).keys()))
        except:
            pass
            
if __name__ == "__main__":
    main()
