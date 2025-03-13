import json
from pathlib import Path
import argparse

def load_structure(file_path):
    """加载目录结构文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_nodes(base_node, target_node, current_path):
    """比较单个目录节点（修正版）"""
    diff_node = {
        "path": current_path,
        "type": "directory",
        "added_files": [],
        "missing_files": [],
        "modified_files": [],
        "subdirectories": {}
    }

    # 比较文件
    base_files = {f["name"]: f for f in base_node.get("files", [])}
    target_files = {f["name"]: f for f in target_node.get("files", [])}

    # 查找新增文件
    for name in target_files:
        if name not in base_files:
            diff_node["added_files"].append(target_files[name])

    # 查找缺失文件
    for name in base_files:
        if name not in target_files:
            diff_node["missing_files"].append(base_files[name])

    # 比较共有文件
    for name in base_files:
        if name in target_files:
            bf = base_files[name]
            tf = target_files[name]
            differences = {}
            for attr in ["size", "modify_date", "create_date"]:
                if bf[attr] != tf[attr]:
                    differences[attr] = {
                        "base": bf[attr],
                        "target": tf[attr]
                    }
            if differences:
                diff_file = bf.copy()
                diff_file.update({
                    "differences": differences,
                    "target_info": tf
                })
                diff_node["modified_files"].append(diff_file)

    # 比较子目录（修正部分）
    base_dirs = {d["name"]: d for d in base_node.get("subdirectories", [])}
    target_dirs = {d["name"]: d for d in target_node.get("subdirectories", [])}

    all_dirs = set(base_dirs.keys()) | set(target_dirs.keys())
    for dir_name in all_dirs:
        dir_path = str(Path(current_path) / dir_name)
        
        if dir_name not in base_dirs:
            # 新增目录
            diff_node["subdirectories"][dir_name] = {
                "path": dir_path,
                "type": "new_directory",
                "target_files": target_dirs[dir_name]["files"]
            }
        elif dir_name not in target_dirs:
            # 删除目录
            diff_node["subdirectories"][dir_name] = {
                "path": dir_path,
                "type": "deleted_directory",
                "base_files": base_dirs[dir_name]["files"]
            }
        else:
            # 递归比较共有目录
            sub_diff = compare_nodes(
                base_dirs[dir_name],
                target_dirs[dir_name],
                dir_path
            )
            if sub_diff is not None:
                diff_node["subdirectories"][dir_name] = sub_diff

    # 判断是否存在有效差异
    has_changes = any([
        diff_node["added_files"],
        diff_node["missing_files"],
        diff_node["modified_files"],
        diff_node["subdirectories"]
    ])
    
    return diff_node if has_changes else None

def main():
    parser = argparse.ArgumentParser(description="结构化目录差异对比工具（修正版）")
    parser.add_argument("base_json", help="基准目录的JSON文件")
    parser.add_argument("target_json", help="对比目录的JSON文件")
    parser.add_argument("output_file", help="差异输出文件路径")
    args = parser.parse_args()

    # 加载目录结构
    base = load_structure(args.base_json)
    target = load_structure(args.target_json)

    # 执行对比
    diff_tree = compare_nodes(base, target, current_path=Path(args.base_json).stem)

    # 保存结果
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(diff_tree, f, indent=2, ensure_ascii=False)

    print(f"结构化差异报告已保存至 {args.output_file}")

if __name__ == "__main__":
    main()