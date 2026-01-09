@echo off
chcp 65001 > nul

:: 读取配置文件中的游戏路径和启动路径
setlocal enabledelayedexpansion

:: 检查config.json是否存在
if not exist "config.json" (
    echo [错误] config.json 文件不存在
    pause
    exit /b 1
)

:: 简单的JSON解析（提取gameFolderPath）
for /f "tokens=2 delims=:" %%a in ('type "config.json" ^| findstr "gameFolderPath"') do (
    set "gameFolderPath=%%a"
    :: 移除引号和空格
    set "gameFolderPath=!gameFolderPath:~2,-1!"
)

:: 提取Bilibili启动路径
for /f "tokens=2 delims=:" %%a in ('type "config.json" ^| findstr "bilibili.*launch" /i') do (
    set "bilibiliLaunch=%%a"
    :: 移除引号和空格
    set "bilibiliLaunch=!bilibiliLaunch:~2,-1!"
)

:: 提取Official启动路径
for /f "tokens=2 delims=:" %%a in ('type "config.json" ^| findstr "official.*launch" /i') do (
    set "officialLaunch=%%a"
    :: 移除引号和空格
    set "officialLaunch=!officialLaunch:~2,-1!"
)

:: 检查游戏路径是否存在
if not exist "!gameFolderPath!" (
    echo [错误] 游戏路径 "!gameFolderPath!" 不存在
    pause
    exit /b 1
)

:: 设置KRSDKConfig路径
set "KRSDKConfigPath=!gameFolderPath!\Client\Binaries\Win64\ThirdParty\KrPcSdk_Mainland\KRSDKRes\KRSDKConfig.json"

:: 检查KRSDKConfig文件是否存在
if not exist "!KRSDKConfigPath!" (
    echo [错误] KRSDKConfig.json 文件不存在: "!KRSDKConfigPath!"
    pause
    exit /b 1
)

:: 确定当前版本
set "current_ver="
set "aim_ver="

:: 查找当前版本
for /f "tokens=1,2 delims=:" %%a in ('type "!KRSDKConfigPath!" ^| findstr "KR_PackageName"') do (
    set "packageName=%%b"
    set "packageName=!packageName:~2,-1!"
    
    if "!packageName!" == "com.kurogame.mingchao.bilibili" (
        set "current_ver=Bilibili"
        set "aim_ver=Official"
    ) else if "!packageName!" == "com.kurogame.mingchao" (
        set "current_ver=Official"
        set "aim_ver=Bilibili"
    )
)

:: 如果无法确定版本
if "!current_ver!" == "" (
    echo [错误] 无法确定当前版本，请检查 KRSDKConfig.json 文件
    pause
    exit /b 1
)

:: 创建必要的目录
if not exist "Bilibili" mkdir "Bilibili"
if not exist "Official" mkdir "Official"

:: 显示信息
cls
echo.
echo 项目地址: https://github.com/Hurry1027/Wuthering-Waves-Official-Bilibili
echo.
echo 当前版本: !current_ver!
echo 请选择操作：
echo 1. 启动 !current_ver! 客户端
echo 2. 备份文件, 切换到!aim_ver! 版本, 最后启动客户端

echo.
set /p "choice=💬 请输入选择 (1/2): "

:: 处理选择
if "!choice!" == "1" (
    :: 启动当前版本客户端
    if "!current_ver!" == "Bilibili" (
        echo.
        echo 🚀 正在启动 !current_ver! 客户端...
        start "" "!bilibiliLaunch!"
    ) else (
        echo.
        echo 🚀 正在启动 !current_ver! 客户端...
        start "" "!officialLaunch!"
    )
    exit /b 0
) else if "!choice!" == "2" (
    :: 继续执行转换流程
    echo.
) else (
    echo 无效选择，程序退出
    pause
    exit /b 0
)

:: 备份当前版本
echo.
set /p "confirm=💬 确认备份当前版本 !current_ver! ? (y/n) "
if /i "!confirm!" == "y" (
    :: 删除旧备份
    set "old_backup_path=!current_ver!\KrPcSdk_Mainland"
    if exist "!old_backup_path!" (
        rmdir /s /q "!old_backup_path!" > nul 2>&1
        if errorlevel 1 (
            echo [删除]❌ 旧备份权限不足，无法删除 !old_backup_path!
            pause
            exit /b 1
        ) else (
            echo [删除]✅ 已移除旧备份 !old_backup_path!
        )
    )

    :: 复制当前版本
    set "source_path=!gameFolderPath!\Client\Binaries\Win64\ThirdParty\KrPcSdk_Mainland"
    if not exist "!source_path!" (
        echo [备份]❌ !current_ver! 源目录不存在
        pause
        exit /b 1
    )

    xcopy "!source_path!" "!old_backup_path!" /e /i /h /k /q > nul 2>&1
    if errorlevel 1 (
        echo [备份]❌ 备份 !current_ver! 失败
        pause
        exit /b 1
    ) else (
        echo [备份]✅ 已备份当前 !current_ver! 版本
    )
) else (
    echo 🚫 已取消备份当前版本 !current_ver!
)

:: 转换到目标版本
echo.
set /p "confirm=💬 确认转换到版本 !aim_ver! ? (y/n) "
if /i "!confirm!" == "y" (
    :: 检查目标版本备份是否存在
    set "target_backup_path=!aim_ver!\KrPcSdk_Mainland"
    if not exist "!target_backup_path!" (
        echo [转换]❌ 目标版本(!aim_ver!) 的备份不存在
        pause
        exit /b 1
    )

    :: 删除当前SDK目录
    set "target_path=!gameFolderPath!\Client\Binaries\Win64\ThirdParty\KrPcSdk_Mainland"
    if exist "!target_path!" (
        rmdir /s /q "!target_path!" > nul 2>&1
        if errorlevel 1 (
            echo [转换]❌ 目标路径权限不足，无法删除文件
            pause
            exit /b 1
        )
    )

    :: 复制目标版本备份
    xcopy "!target_backup_path!" "!target_path!" /e /i /h /k /q > nul 2>&1
    if errorlevel 1 (
        echo [转换]❌ 复制 !aim_ver! 备份失败
        pause
        exit /b 1
    ) else (
        echo [转换]✅ 已转换到 !aim_ver! 版本
        echo.
    )

    :: 启动目标版本客户端
    if "!aim_ver!" == "Bilibili" (
        echo 🚀 正在启动 !aim_ver! 客户端...
        start "" "!bilibiliLaunch!"
    ) else (
        echo 🚀 正在启动 !aim_ver! 客户端...
        start "" "!officialLaunch!"
    )
    exit /b 0
) else (
    echo 🚫 转换操作已取消
    pause
    exit /b 0
)

endlocal
