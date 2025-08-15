# upload_to_paratranz.py

import json
import os
import re
from pathlib import Path
import requests

# --- 配置 ---
# 从环境变量获取，确保在运行前设置
TOKEN: str = os.getenv("PARATRANZ_API_TOKEN", "")
PROJECT_ID: str = os.getenv("PROJECT_ID", "")

if not TOKEN or not PROJECT_ID:
    raise EnvironmentError("请设置环境变量 PARATRANZ_API_TOKEN 和 PROJECT_ID。")

SOURCE_DIR = Path("Source")
API_URL = f"https://paratranz.cn/api/projects/{PROJECT_ID}/files"
# --- 配置结束 ---

def lang_to_dict(file_path: Path) -> dict[str, str]:
    """将 .lang 文件内容解析为字典"""
    lang_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                lang_dict[key.strip()] = value.strip()
    return lang_dict

def upload_file_to_paratranz(path_in_paratranz: str, content: str):
    """上传单个文件到 Paratranz"""
    headers = {"Authorization": TOKEN}
    files = {
        "file": (path_in_paratranz, content, "application/json"),
        "path": (None, str(Path(path_in_paratranz).parent)),
    }

    try:
        response = requests.post(API_URL, headers=headers, files=files)
        response.raise_for_status()
        print(f"✅ 成功上传: {path_in_paratranz}")
        print(f"   响应: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 上传失败: {path_in_paratranz}")
        print(f"   错误: {e}")
        if e.response:
            print(f"   响应内容: {e.response.text}")

def main():
    """主函数，遍历、转换并上传文件"""
    if not SOURCE_DIR.is_dir():
        print(f"错误: 源目录 '{SOURCE_DIR}' 不存在。")
        return

    print(f"正在从 '{SOURCE_DIR}' 目录查找 en_us.lang 文件...")

    for lang_file in SOURCE_DIR.rglob("*.lang"):
        if lang_file.name != "en_us.lang":
            continue

        print(f"\n ditemukan: {lang_file}")

        # 1. 将 .lang 文件转换为字典
        translation_dict = lang_to_dict(lang_file)
        if not translation_dict:
            print("   文件为空或无效，跳过。")
            continue

        # 2. 将字典转换为 JSON 字符串
        json_content = json.dumps(translation_dict, ensure_ascii=False, indent=4)

        # 3. 确定在 Paratranz 上的路径 (e.g., Source/assets/mod/lang/en_us.lang -> assets/mod/lang/en_us.json)
        relative_path = lang_file.relative_to(SOURCE_DIR)
        paratranz_path = relative_path.with_suffix(".json").as_posix()

        # 4. 上传文件
        upload_file_to_paratranz(paratranz_path, json_content)

if __name__ == "__main__":
    main()