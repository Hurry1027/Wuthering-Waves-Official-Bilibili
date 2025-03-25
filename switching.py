#-*- coding: utf-8 -*-
import json
import os
import subprocess
import shutil
from pathlib import Path
import argparse
import datetime
import sys

CONFIG_FILE = "sync_config.json"
STATE_FILE = "sync_state.json"

class SyncSystem:
    def __init__(self):
        self.config = self.load_config()
        self.state = self.load_state()
        self.current_version = None
        self.other_version = None
        
    def load_config(self):
        """加载配置文件"""
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        # 转换路径为Path对象
        config['gameFolderPath'] = Path(config['gameFolderPath'])
        config['client_launch_paths'] = {k: Path(v) for k,v in config['client_launch_paths'].items()}
        config['backup_dir'] = Path(config['backup_dir'])
        config['max_backups'] = config.get('max_backups', 1)
        return config
    
    def load_state(self):
        """加载状态文件"""
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"current_ver": None, "backups": {}}

    def save_state(self):
        """保存状态文件"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def detect_version(self):
        """确定当前版本"""
        if not self.state['current_ver']:
            print("⚠️ 初次使用，需要初始化版本")
            ver = input("💬 请输入当前版本 (Bilibili/Official): ").strip()
            while ver not in ["Bilibili", "Official"]:
                print(f"错误：{ver} 不是有效版本")
                ver = input("💬 请输入当前版本 (Bilibili/Official): ").strip()
            self.state['current_ver'] = ver
            self.save_state()
        
        self.current_version = self.state['current_ver']
        self.other_version = "Official" if self.current_version == "Bilibili" else "Bilibili"
        print("\n")
        print("###############################")
        print(f"当前版本: {self.current_version}")
        print("###############################")

    def scan_current_version(self):
        """扫描当前版本目录"""
        print("\n🔍 正在扫描当前版本...")
        ver_dir = self.config['gameFolderPath']
        output_file = f"{self.current_version}.json"
        
        # 调用scan.py进行扫描
        cmd = [
            "python", "scan.py",
            str(ver_dir),
            output_file,
        ]
        
        subprocess.run(cmd, check=True)
        print(f"扫描结果已保存至 {output_file}")

    def generate_diff(self):
        """生成差异报告"""
        # if input("💬 是否生成差异报告？(y/n) ").lower() != 'y':
        #     print("已取消生成差异报告")
        #     return
        other_version_json = Path(f"{self.other_version}.json")
        current_version_json = Path(f"{self.current_version}.json")
        if not other_version_json.exists() or not current_version_json.exists():
            print(f"\n❌ 暂无法生成差异报告，版本目录信息：{self.other_version}.json 缺失, 现在请切换到 {self.other_version} 的客户端修复文件, 然后手动更改sync_state.json中的current_ver为{self.other_version}，重新执行此程序")
            sys.exit(0)
        print("\n🔀 正在生成差异报告...")
        cmd = [
            "python", "structured_diff.py",
            f"{self.other_version}.json",
            f"{self.current_version}.json",
            "structured_diff.json"
        ]
        subprocess.run(cmd, check=True)
        print("差异报告已更新")

    def calculate_backup(self):
        """计算需要备份的文件"""
        with open("structured_diff.json", 'r') as f:
            diff = json.load(f)
        
        backup_files = []
        total_size = 0
        target_dir = self.config['gameFolderPath']
        ignore_list = self.config.get('ignore_list', [])

        with open("backup_plan.txt", "w") as log_file:
            def walk(node):
                nonlocal total_size
                current_path = Path(node['path'])
                relative_path = Path(*current_path.parts[1:])
                
                # 跳过被忽略的目录
                current_relative = relative_path.as_posix()
                if any(ignored in current_relative for ignored in ignore_list):
                    return
                
                # 处理需要备份的文件（新增忽略检查）
                for f in node.get('modified_files', []):
                    file_path = target_dir / relative_path / f['name']
                    file_relative = file_path.relative_to(target_dir).as_posix()
                    if file_path.exists() and not any(ignored in file_relative for ignored in ignore_list):
                        backup_files.append(file_path)
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        log_file.write(f"{file_path.as_posix()}, ({file_size/1024/1024:.2f}MB)\n")
                
                for f in node.get('missing_files', []):
                    file_path = target_dir / relative_path / f['name']
                    file_relative = file_path.relative_to(target_dir).as_posix()
                    if file_path.exists() and not any(ignored in file_relative for ignored in ignore_list):
                        backup_files.append(file_path)
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        log_file.write(f"{file_path.as_posix()}, ({file_size/1024/1024:.2f}MB)\n")
                
                # 递归子目录
                for sub in node.get('subdirectories', {}).values():
                    walk(sub)

            walk(diff)
        
        return backup_files, total_size

    def perform_backup(self):
        """执行备份操作"""
        print("\n💻 正在计算备份文件大小..")
        backup_files, total_size = self.calculate_backup()
        if not backup_files:
            print("\n✅ 没有需要备份的文件")
            return
        
        print(f"⚠️ 准备备份 {self.current_version} 版本 | 需要备份 {len(backup_files)} 个文件，共 {total_size/1024/1024:.2f} MB | 你可以手动打开backup_plan.txt查看具体备份文件")
        if input("💬 是否执行备份？(推荐客户端更新后再执行备份, 平时选n就可以)(y/n) ").lower() != 'y':
            print("已取消备份")
            return

        # 创建带时间戳的备份目录
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.config['backup_dir'] / self.current_version / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        # 执行备份
        for src in backup_files:
            relative = src.relative_to(self.config['gameFolderPath'])
            dst = backup_path / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"↩️ 已备份: {src} → {dst}")

        # 更新状态文件
        self.state['backups'][self.current_version] = {
            "timestamp": timestamp,
            "path": str(backup_path),
            "file_count": len(backup_files),
            "total_size": total_size
        }

        # 备份数量限制
        backup_dir = self.config['backup_dir'] / self.current_version
        if backup_dir.exists():
            # 获取所有备份并按时间排序
            backups = sorted(backup_dir.iterdir(), key=os.path.getmtime)
            # 计算需要保留的数量（保留最新N个）
            max_keep = self.config['max_backups']
            if len(backups) > max_keep:
                # 删除旧备份
                for old_backup in backups[:-max_keep]:
                    shutil.rmtree(old_backup)
                    print(f"♻️ 已清理旧备份: {old_backup}")
        self.save_state()
    
    def check_conversion(self):
        """检查转换可行性"""
        other_json = f"{self.other_version}.json"
        if not Path(other_json).exists():
            print(f"\n❌ 缺少 {self.other_version} 版本信息文件")
            print("请先切换到另一版本并运行扫描")
            return False

        # 获取目标版本的最新备份路径
        target_version = self.other_version
        backup_info = self.state['backups'].get(target_version)
        if not backup_info:
            print(f"❌ 找不到 {target_version} 的可用备份, 转换失败。你需要再次手动切换到该版本, 然后手动更改sync_state.json中的current_ver为{target_version}，重新执行此程序")
            sys.exit(0)
            return False
        return True

    def generate_conversion_plan(self):
        """生成转换计划报告"""
        plan_path = "conversion_plan.txt"
        total_ops = 0
        total_size = 0
        
        # 获取目标版本的最新备份路径
        target_version = self.other_version
        backup_info = self.state['backups'].get(target_version)
        backup_dir = Path(backup_info['path'])

        with open("structured_diff.json") as f, open(plan_path, "w") as report:
            diff = json.load(f)
            ignore_list = self.config.get('ignore_list', [])
            
            # 更新操作说明
            report.write("=== 计划转换操作 ===\n")
            report.write("操作类型说明：\n")
            report.write("[删除] 当前版本多余文件\n")
            report.write("[恢复] 从备份恢复文件\n\n")  # 修改操作类型描述
            
            def analyze(node):
                nonlocal total_ops, total_size
                current_path = Path(node['path'])
                relative_path = current_path.relative_to(target_version)  # 新增相对路径计算
                # 忽略检查
                current_relative = relative_path.as_posix()
                if any(ignored in current_relative for ignored in ignore_list):
                    return

                # 处理删除操作（缺失文件）
                # for f in node.get('missing_files', []):
                #     target_file = self.config['gameFolderPath'] / current_path / f['name']
                #     report.write(f"[删除] {target_file.as_posix()}\n")
                #     total_ops += 1
                
                # 合并处理新增文件和修改文件
                for f in node.get('new_files', []) + node.get('modified_files', []):
                    relative_path = current_path.relative_to(target_version)
                    backup_file = backup_dir / relative_path / f['name']
                    file_relative = (relative_path / f['name']).as_posix()  # 新增文件路径检查
                    
                    # 文件级忽略检查
                    if any(ignored in file_relative for ignored in ignore_list):
                        continue
                    if backup_file.exists():
                        file_size = backup_file.stat().st_size
                        operation_type = "新增" if f in node.get('new_files', []) else "更新"
                        report.write(f"[恢复] ({operation_type}) {backup_file.relative_to(backup_dir)} ({file_size/1024/1024:.2f}MB)\n")
                        total_ops += 1
                        total_size += file_size
                    else:
                        report.write(f"[警告] 缺失备份文件: {backup_file.relative_to(backup_dir)}\n")
                
                # 递归子目录（保持不变）
                for sub in node.get('subdirectories', {}).values():
                    analyze(sub)
            
            analyze(diff)
            report.write(f"\n总计操作: {total_ops} 个文件，需恢复 {total_size/1024/1024:.2f}MB")
        return plan_path

    def run(self):
        """主运行流程"""
        self.detect_version()
        
         # 新增启动菜单
        print(f"\n当前版本: {self.current_version}")
        print("请选择操作：")
        print(f"1. 启动 {self.current_version} 客户端")
        print(f"2. 备份文件, 切换到{self.other_version} 版本, 最后启动客户端")
        choice = input("💬 请输入选择 (1/2): ").strip()
        
        if choice == '1':
            launch_path = self.config['client_launch_paths'][self.current_version]
            print(f"\n🚀 正在启动 {self.current_version} 客户端...")
            os.system(f'start "" "{str(launch_path).strip().strip('\u202a').rstrip('\u202c')}"')
            sys.exit(0)
            return
        elif choice == '2':
            # 执行原有转换流程
            pass
        else:
            print("无效选择，程序退出")
            sys.exit(0)
            return

        # 步骤1：扫描当前版本
        self.scan_current_version()
        
        # 步骤2：生成差异报告
        try:
            self.generate_diff()
        except SystemExit as e:
            print(f"程序因必要文件缺失退出，退出码: {e.code}")
            return
        except subprocess.CalledProcessError:
            print("\n❌ 无法生成差异报告，可能缺少另一版本数据")
            print(f"请确认 {self.other_version}.json 是否存在")
            return

        # 步骤3：备份操作
        self.perform_backup()

        # 删除备份计划文件
        if os.path.exists("backup_plan.txt"):
            os.remove("backup_plan.txt")
            print(f"🗑️ 已清理备份计划文件: backup_plan.txt")

        # 步骤4：检查转换可行性
        if not self.check_conversion():
            return

        # 步骤5：执行转换
        #if input(f"\n💬 是否生成转换到 {self.other_version} 的计划？(y/n) ").lower() == 'y':
        print("\n📝 正在生成转换计划...")
        plan_file = self.generate_conversion_plan()
        print(f"⚠️ 转换计划已保存至 {plan_file}")
            
        # try:
        #     import platform
        #     if platform.system() == 'Windows':
        #         subprocess.Popen(['start', plan_file], shell=True)
        #     elif platform.system() == 'Darwin':
        #         subprocess.Popen(['open', plan_file])
        #     else:
        #         subprocess.Popen(['xdg-open', plan_file])
        # except Exception as e:
        #     print(f"❌ 无法打开转换计划文件: {e}")

        print("请核对转换计划文件中的操作项, 再进行下一步")
        if input(f"💬 确认转换到版本 {self.other_version} ? (y/n) ").lower() != 'y':
            print("🚫 转换操作已取消")
        else:
            print("\n🚀 开始执行版本转换...")
            # 新增：获取目标版本的最新备份路径
            target_version = self.other_version
            if target_version not in self.state['backups']:
                print(f"❌ 找不到 {target_version} 的可用备份")
                return
                
            # 获取最新备份路径
            backup_info = self.state['backups'][target_version]
            backup_dir = Path(backup_info['path'])
            
            # 递归恢复文件的方法
            def restore_from_backup(node, base_path):
                current_dir = self.config['gameFolderPath'] / base_path
                current_dir.mkdir(parents=True, exist_ok=True)
                ignore_list = self.config.get('ignore_list', [])

                # 处理需要删除的文件
                # for f in node.get('missing_files', []):
                #     file_to_delete = current_dir / f['name']
                #     file_relative = (base_path / f['name']).as_posix()  # 新增相对路径
                #     if any(ignored in file_relative for ignored in ignore_list):
                #         continue  # 跳过被忽略的文件

                #     if file_to_delete.exists():
                #         file_to_delete.unlink()
                #         print(f"🗑️ 已删除多余文件: {file_to_delete}")

                # 处理需要恢复的文件（包括新增和修改）
                for f in node.get('new_files', []) + node.get('modified_files', []):
                    backup_file = backup_dir / base_path / f['name']
                    target_file = current_dir / f['name']
                    file_relative = (base_path / f['name']).as_posix()  # 新增相对路径
                    if any(ignored in file_relative for ignored in ignore_list):
                        continue  # 跳过被忽略的文件

                    if backup_file.exists():
                        shutil.copy2(backup_file, target_file)
                        op_type = "新增" if f in node.get('new_files', []) else "更新"
                        print(f"🔄 [{op_type}] 从备份恢复: {target_file}")
                    else:
                        print(f"⚠️ 备份文件缺失: {backup_file}")
                
                # 递归处理子目录
                for sub_name, sub_node in node.get('subdirectories', {}).items():
                    restore_from_backup(sub_node, base_path / sub_name)

            # 读取差异报告并应用恢复
            with open("structured_diff.json", 'r') as f:
                diff_data = json.load(f)
                restore_from_backup(diff_data, Path())
            
            # 更新版本状态
            self.state['current_ver'] = target_version
            self.save_state()
            print(f"✅ 已成功转换至 {target_version} 版本")

            # 转换完成后启动新版本客户端
            launch_path = self.config['client_launch_paths'][self.other_version]
            print(f"\n🚀 正在启动 {self.other_version} 客户端...")
            os.system(f'start "" "{str(launch_path).strip().strip('\u202a')}"')

        # 删除转换计划文件
        if os.path.exists("conversion_plan.txt"):
            os.remove("conversion_plan.txt")
            print(f"🗑️ 已清理转换计划文件: conversion_plan.txt")
        
        print("\n 程序结束！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智能版本同步系统")
    args = parser.parse_args()
    
    system = SyncSystem()
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n操作已取消")
    # except Exception as e:
    #     print(f"\n❌ 发生错误: {str(e)}")
    #     print("请检查配置文件或目录状态")
