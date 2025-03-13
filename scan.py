import argparse
from pathlib import Path
import datetime
import json

def get_directory_structure(root_dir):
    """递归获取目录结构信息"""
    dir_info = {
        "name": root_dir.name,
        "type": "directory",
        "files": [],
        "subdirectories": []
    }
    
    for item in root_dir.iterdir():
        # 跳过符号链接
        if item.is_symlink():
            continue
        
        try:
            if item.is_file():
                # 获取文件信息
                stat = item.stat()
                file_info = {
                    "name": item.name,
                    "type": "file",
                    "create_date": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modify_date": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size
                }
                dir_info["files"].append(file_info)
                
            elif item.is_dir():
                # 递归处理子目录
                subdir_info = get_directory_structure(item)
                dir_info["subdirectories"].append(subdir_info)
                
        except Exception as e:
            print(f"Error processing {item}: {str(e)}")
    
    return dir_info

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="目录结构导出工具")
    parser.add_argument("root_dir", help="要扫描的根目录")
    parser.add_argument("output_file", help="输出的JSON文件路径")
    args = parser.parse_args()

    # 验证目录有效性
    root_path = Path(args.root_dir).resolve()
    if not root_path.is_dir():
        print(f"错误：{args.root_dir} 不是有效目录")
        exit(1)

    # 生成目录结构
    structure = get_directory_structure(root_path)
    
    # 保存为JSON文件
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    
    print(f"目录结构已保存至 {args.output_file}")