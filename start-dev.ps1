# 启动开发环境的 Windows Terminal 脚本
# 在一个窗口中打开两个标签页，分别运行前端和后端

$projectRoot = $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

# 构建参数数组
$allArgs = @(
    "new-tab",
    "-d", $backendDir,
    "powershell",
    "-NoExit",
    "-Command", ".venv\Scripts\python.exe app.py",
    ";",
    "new-tab",
    "-d", $frontendDir,
    "powershell",
    "-NoExit",
    "-Command", "npm run dev"
)

# 执行 wt
& wt $allArgs
