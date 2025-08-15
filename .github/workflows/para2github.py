# download_from_paratranz.py

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any
import requests

# --- 配置 ---
# 从环境变量获取
TOKEN: str = os.getenv("PARATRANZ_API_TOKEN", "")
PROJECT_ID: str = os.getenv("PROJECT_ID", "")

if not TOKEN or not PROJECT_ID:
    raise EnvironmentError("请设置环境变量 PARATRANZ_API_TOKEN 和 PROJECT_ID。")

SOURCE_DIR = Path("Source")
OUTPUT_DIR = Path("CNPack")
API_BASE_URL = "https://paratranz.cn/api/projects/"
# --- 配置结束 ---

def fetch_api(url: str) -> Any:
    """通用 API 请求函数"""
    headers = {"Authorization": TOKEN}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_all_files() -> List[Dict[str, Any]]:
    """获取项目中的所有文件列表"""
    url = f"{API_BASE_URL}{PROJECT_ID}/files"
    print("正在从 Paratranz 获取文件列表...")
    files = fetch_api(url)
    print(f"✅ 成功获取 {len(files)} 个文件。")
    return files

def get_translation(file_id: int) -> Dict[str, str]:
    """获取指定文件的翻译内容"""
    url = f"{API_BASE_URL}{PROJECT_ID}/files/{file_id}/translation"
    translations = fetch_api(url)
    
    processed_dict = {}
    for item in translations:
        key = item["key"]
        # 优先使用翻译，如果翻译为空或处于特定阶段，则使用原文
        translation = item.get("translation", "")
        original = item.get("original", "")
        final_value = original if item["stage"] in [0, -1, 2] or not translation else translation
        
        # 处理 Paratranz 导出的特殊字符
        final_value = re.sub(r"&#92;", r"\\", final_value)
        final_value = final_value.replace("\\\\n", "\\n") # 修正可能出现的双重转义

        processed_dict[key] = final_value
        
    return processed_dict

def save_as_lang(translated_dict: Dict[str, str], source_path: Path, output_path: Path):
    """
    将翻译字典保存为 .lang 文件，并尽可能保留源文件的顺序和注释。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not source_path.exists():
        print(f"⚠️ 警告: 源文件 {source_path} 不存在。将按字母顺序保存。")
        with open(output_path, "w", encoding="utf-8") as f:
            sorted_keys = sorted(translated_dict.keys())
            for key in sorted_keys:
                f.write(f"{key}={translated_dict[key]}\n")
        return

    print(f"   正在根据 {source_path} 的顺序和注释生成文件...")
    with open(source_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                # 保留空行和注释
                f_out.write(line)
                continue
            
            if "=" in stripped_line:
                key = stripped_line.split("=", 1)[0].strip()
                if key in translated_dict:
                    # 使用翻译后的值写入
                    f_out.write(f"{key}={translated_dict[key]}\n")
                else:
                    # 如果翻译中没有这个key，保留原文（可选）
                    f_out.write(line)

def main():
    """主函数，下载、转换并保存翻译文件"""
    all_files = get_all_files()

    for file_info in all_files:
        file_id = file_info["id"]
        # Paratranz 中的路径，例如: assets/minecraft/lang/en_us.json
        paratranz_path_str = file_info["name"]
        
        print(f"\n正在处理: {paratranz_path_str} (ID: {file_id})")
        
        # 1. 获取翻译
        translated_content = get_translation(file_id)
        
        # 2. 计算输出路径和对应的源文件路径
        # assets/minecraft/lang/en_us.json -> CNPack/assets/minecraft/lang/zh_cn.lang
        output_path = OUTPUT_DIR / Path(paratranz_path_str).parent / "zh_cn.lang"
        # assets/minecraft/lang/en_us.json -> Source/assets/minecraft/lang/en_us.lang
        source_path = SOURCE_DIR / Path(paratranz_path_str).with_name("en_us.lang")

        # 3. 保存为 .lang 文件
        save_as_lang(translated_content, source_path, output_path)
        print(f"✅ 已保存至: {output_path}")
        
    print("\n🎉 所有文件处理完毕！")

if __name__ == "__main__":
    main()