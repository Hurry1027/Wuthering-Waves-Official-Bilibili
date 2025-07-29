import json
import os
import sys
from pathlib import Path
import shutil

# 读取配置
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
config['gameFolderPath'] = Path(config['gameFolderPath'])
config['client_launch_paths'] = {k: Path(v) for k,v in config['client_launch_paths'].items()}

KRSDKConfig_path = Path(config['gameFolderPath']) / 'Client/Binaries/Win64/ThirdParty/KrPcSdk_Mainland/KRSDKRes/KRSDKConfig.json'
with open(KRSDKConfig_path, 'r', encoding='utf-8') as f:
    KRSDKConfig = json.load(f)
if (KRSDKConfig['KR_PackageName'] == 'com.kurogame.mingchao.bilibili'):
    current_ver = 'Bilibili'
    aim_ver = 'Official'
elif (KRSDKConfig['KR_PackageName'] == 'com.kurogame.mingchao'):
    current_ver = 'Official'
    aim_ver = 'Bilibili'
else:
    print(f"配置文件错误, {str(KRSDKConfig_path)}文件错误")
    sys.exit(1)

# 初始化
Path('Bilibili').mkdir(parents=True, exist_ok=True)
Path('Official').mkdir(parents=True, exist_ok=True)

# 启动
print(f'\n项目地址: https://github.com/Hurry1027/Wuthering-Waves-Official-Bilibili')
print(f"\n当前版本: {current_ver} {KRSDKConfig['KR_GameVersion']}")
print("请选择操作：")
print(f"1. 启动 {current_ver} 客户端")
print(f"2. 备份文件, 切换到{aim_ver} 版本, 最后启动客户端")
choice = input("💬 请输入选择 (1/2): ").strip()
if choice == '1':
    launch_path = config['client_launch_paths'][current_ver]
    print(f"\n🚀 正在启动 {current_ver} 客户端...")
    os.system(f'start "" "{str(launch_path).strip().strip('\u202a').rstrip('\u202c')}"')
    sys.exit(0)
elif choice == '2':
    # 执行原有转换流程
    pass
else:
    print("无效选择，程序退出")
    sys.exit(0)
print('')


# 备份
if input(f"💬 确认备份当前版本 {current_ver} ? (y/n) ").lower() == 'y':
    # 删除旧备份
    old_backup_path = Path(current_ver) / 'KrPcSdk_Mainland'
    try:
        shutil.rmtree(old_backup_path)
    except FileNotFoundError:
        pass
    except PermissionError:
        print(f"[删除]❌ 旧备份权限不足，无法删除 {old_backup_path}")
        sys.exit(1)
    print(f"[删除]✅ 已移除旧备份 {str(old_backup_path)}")

    try:
        shutil.copytree(config['gameFolderPath'] / 'Client/Binaries/Win64/ThirdParty/KrPcSdk_Mainland', old_backup_path)
    except FileNotFoundError:
        print(f"[备份]❌ {current_ver} 源目录不存在")
        sys.exit(1)
    except PermissionError:
        print(f"[备份]❌ {current_ver} 权限不足，无法备份")
        sys.exit(1)
    except Exception as e:
        print(f"[备份]❌ 备份 {current_ver} 失败: {e}")
        sys.exit(1)
    print(f"[备份]✅ 已备份当前 {current_ver} 版本")
else:
    print(f"🚫 已取消备份当前版本 {current_ver} ")


# 转换
if input(f"💬 确认转换到版本 {aim_ver} ? (y/n) ").lower() == 'y':
    if (not (Path(aim_ver) / 'KrPcSdk_Mainland').exists()):
        print(f"[转换]❌ 目标版本({aim_ver}) 的备份不存在")
        sys.exit(1)

    try:
        shutil.rmtree(config['gameFolderPath'] / 'Client/Binaries/Win64/ThirdParty/KrPcSdk_Mainland')
    except FileNotFoundError:
        pass
    except PermissionError:
        print(f"[转换]❌ 目标版本({aim_ver}) 的权限不足，无法删除文件并更新文件")
        sys.exit(1)

    try:
        shutil.copytree(Path(aim_ver) / 'KrPcSdk_Mainland', config['gameFolderPath'] / 'Client/Binaries/Win64/ThirdParty/KrPcSdk_Mainland')
    except FileNotFoundError:
        print(f"[转换]❌ {aim_ver} 的备份不存在")
        sys.exit(1)
    except PermissionError:
        print(f"[转换]❌ {aim_ver} 的备份权限不足，无法备份")
        sys.exit(1)
    except Exception as e:
        print(f"[转换]❌ {aim_ver} 的备份移动时失败: {e}")
        sys.exit(1)
    print(f"[转换]✅ 已转换到 {aim_ver} 版本")
    print('')

    # 启动
    launch_path = config['client_launch_paths'][aim_ver]
    print(f"\n🚀 正在启动 {aim_ver} 客户端...")
    os.system(f'start "" "{str(launch_path).strip().strip('\u202a').rstrip('\u202c')}"')
    sys.exit(0)
else:
    print("🚫 转换操作已取消")
    sys.exit(0)


    