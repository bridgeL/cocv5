# 任务计划：Agent MCP工具调用系统

## 任务拆解

### 任务1：MCP工具实现
**文件：** `mcp/get_apple_cnt.py`, `mcp/get_apple_price.py`

**步骤：**
1. 创建mcp目录
2. 实现get_apple_cnt工具（返回1/2/3随机数）
3. 实现get_apple_price工具（返回10/20/40随机数）
4. 定义工具描述信息（供OpenAI function calling使用）

**验收标准：**
- 工具函数可独立调用并返回正确范围的随机数
- 包含完整的tool schema描述

---

### 任务2：记忆管理模块
**文件：** `memory.py`

**步骤：**
1. 设计Memory类，按session_id隔离存储
2. 实现消息追加方法（支持system/user/assistant/tool类型）
3. 实现获取完整对话历史方法
4. 确保memory全量保留不做裁剪

**验收标准：**
- 不同session_id数据隔离
- 支持存储OpenAI格式的messages
- 支持存储tool调用相关的message

---

### 任务3：Agent核心逻辑
**文件：** `agent.py`

**步骤：**
1. 导入MCP工具和Memory模块
2. 定义ToolCall和ToolResult数据结构
3. 实现Agent类：
   - `__init__`: 初始化ws连接、memory实例、openai客户端
   - `chat`: 主对话方法，处理流式响应
   - `_handle_stream`: 处理流式chunk，区分msg和tool类型
   - `_handle_tool_calls`: 处理工具调用，执行MCP并返回结果
4. 实现create_agent工厂函数

**流式处理逻辑：**
```
接收用户消息
  ↓
调用OpenAI API（启用function calling）
  ↓
流式接收chunk
  ├─ msg类型 → 立即ws发送
  └─ tool类型 → 缓存拼接
      ↓
    完整后ws发送(tool_start)
      ↓
    调用MCP工具
      ↓
    ws发送结果(tool_result)
      ↓
    将结果加入memory
      ↓
    再次调用AI获取最终回复
```

**验收标准：**
- 支持自主决策调用工具
- msg类型chunk实时流式发送
- tool类型chunk完整后处理
- 工具结果正确返回给AI继续对话

---

### 任务4：集成到WebSocket服务
**文件：** 修改 `app.py`

**步骤：**
1. 导入create_agent
2. 在handle_websocket中创建agent实例
3. 处理chat类型消息时调用agent.chat()
4. 新增agent_chat消息类型支持session_id

**验收标准：**
- WebSocket连接可正常创建agent
- 支持带session_id的对话请求
- 消息格式符合feature.md规范

---

### 任务5：测试验证
**步骤：**
1. 自测工具函数正确性
2. 自测memory隔离性
3. 自测Agent流式响应
4. 自测工具调用链路

**验收标准：**
- 所有功能按feature.md验收标准通过

---

## 开发顺序

1. 任务1 → 任务2 → 任务3 → 任务4 → 任务5

## 风险点

- OpenAI function calling流式响应中tool call的delta处理需要小心
- session_id的传递和memory的生命周期管理
