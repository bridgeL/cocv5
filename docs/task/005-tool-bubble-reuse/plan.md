# 任务计划：Tool气泡复用

## 任务列表

### 1. 修改前端 tool_start 处理逻辑
- **文件**: `index.html`
- **函数**: `addToolCall(toolCalls)`
- **修改内容**:
  - 为每个工具气泡添加 `data-tool-id` 属性，存储 `tool_call_id`
  - 在 HTML 结构中预留结果展示区域（默认隐藏）
  - 为状态徽章添加 `data-status` 属性便于后续更新

### 2. 修改前端 tool_end 处理逻辑
- **文件**: `index.html`
- **函数**: `addToolResult(results)`
- **修改内容**:
  - 不再创建新的 div，而是根据 `tool_call_id` 查找已有的工具气泡
  - 更新状态徽章的文本和样式（"调用中" → "成功"/"失败"）
  - 显示结果区域并填充数据

### 3. 自测
- 启动应用，测试同时调用多个工具的场景
- 验证结果是否正确填充到对应的气泡中
- 验证状态更新是否正确

## 变更文件
- `index.html`: 修改 `addToolCall` 和 `addToolResult` 函数
