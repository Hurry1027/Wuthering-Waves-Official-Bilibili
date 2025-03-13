## 项目介绍

本程序实现鸣潮Bilibili与官方客户端版本间的备份以及快捷转换，省去了转换时需要重新读盘下载修复游戏文件的操作。

### 核心功能
- 文件目录结构扫描（scan.py）
- 文件目录差异分析（structured_diff.py）
- 版本备份及转换（switching.py）

### 应用场景
- 有B服和官服两个账号需要频繁切换的电脑端玩家。

### 系统组成
| 模块 | 功能 |
|------|------|
| 鸣潮B服官服转换及启动工具.bat | 一键启动 |
| switching.py | 程序入口 |
| scan.py | 目录结构扫描 |
| structured_diff.py | 差异分析 |
| sync_state.json | 状态文件(识别当前是B服还是官服) |
| sync_config.json | 配置文件 |



### 1. 安装Python
Python是运行 switching.py 文件的基础，你可以从Python官方网站下载并安装Python。

- 步骤 ：
  1. 访问 [Python官方下载页面](https://www.python.org/) 。
  2. 根据你的操作系统（Windows、Mac OS、Linux）选择合适的Python版本（建议选择Python 3.7及以上版本）进行下载。
  3. 运行下载的安装程序，在安装过程中，确保勾选 “Add Python to PATH” 选项，这将允许你在命令行中直接使用Python。
  4. 按照安装向导的提示完成安装。
  5. 安装完成后，你可以通过在命令行中输入 python --version 来验证Python是否成功安装。
### 2. 下载官服和B服客户端
  1. 分别下载官服和B服客户端
  2. 打开设置，将游戏目录设为相同目录

### 3. 填写配置文件
- 步骤 ：
  1. 打开 sync_config.json 文件。
  2. 根据你的实际情况，修改以下配置项：
      - “gameFolderPath”: 设置游戏目录(Wuthering Waves Game文件夹)。
      - ”client_launch_paths“: 分别设置B服客户端和官服客户端启动路径。
      - “ignore_list“: 设置版本转换时需要忽略的文件或文件夹。
      - ”backup_dir“: 设置备份文件存放路径。
      - “max_backups“: 设置最大备份文件数量。
  3. 保存并关闭 sync_config.json 文件。

### 4. 运行 鸣潮B服官服转换及启动工具.bat 或 运行 switching.py
- 你可以直接运行 鸣潮B服官服转换及启动工具.bat ，它会自动运行switching.py。
- switching.py运行步骤 ：
  1. 打开命令提示符（Windows）或终端（Mac OS、Linux）。
  2. 使用 cd 命令切换到 switching.py 文件所在的目录。例如：
  3. 运行 switching.py 文件：
     ```bash
     python switching.py
      ```
### 5. 初始化流程
初始化流程中需要你手动转换两次版本：
1. 确定当前版本 ：初次使用，程序会提示你输入当前客户端版本（Bilibili或Official），这里假如你输入了Bilibili。
2. 扫描当前版本 ：程序会调用 scan.py 扫描当前版本目录，并将结果保存到 Bilibili.json 文件中，此时由于没有另一个版本的文件信息, 程序提前退出。
3. 手动切换到Official版本（官服）：打开官方客户端修复文件， 然后手动更改sync_state.json中的current_ver为Official。
4. 对官服备份：重新执行此程序，选择备份文件并转换, 确认备份当前文件，**此时完成了对官服的备份**。
5. 对B服备份：然后程序提示“找不到 Bilibili 版本的可用备份”，你需要再次手动切换到Bilibili版本（打开B服客户端修复文件），然后再次执行此程序，确认备份当前文件，**此时完成了对B服的备份**，初始化工作结束。你可以选择继续生成转换计划并转换为官服，或者退出程序。

### 6. 程序转换流程
- 步骤 ：
  1. 运行 switching.py 后，程序将按照以下步骤执行：
  2. 扫描当前版本 ：程序会调用 scan.py 扫描当前版本目录，并将结果保存到 Bilibili.json 文件中。
  3. 生成差异文件 ：程序会调用 structured_diff.py 生成差异文件，将差异信息保存到 structured_diff.json 文件中。
  4. 执行备份(可跳过) ：程序会根据差异文件执行备份操作，并将备份文件保存到 backup 目录中，一般在客户端更新后再选择执行备份，平时选择否就行了。
  5. 生成转换计划 ：程序会根据差异文件生成转换计划，并将计划保存到 conversion_plan.txt 文件中，你可以查看程序会复制和覆盖的文件。
  6. 执行转换计划 ：程序会根据转换计划执行版本转换操作。
  7. 完成转换 ：程序将提示转换完成，并打开相应客户端。

### 6. 注意事项
- 初始化流程需认真按步骤进行，如果操作错误需要重来。
- 程序暂无法自动识别是哪个版本的客户端，仅依赖sync_state.json中的配置来区分B服和官服，所以请谨慎填写。
- 因为程序原理是对比差异进行备份，所以不保证程序稳定性。
- 如果本程序出错导导致游戏无法启动，用客户端修复文件即可。
- **如果要转载至其他平台，请先发issue申请授权**。