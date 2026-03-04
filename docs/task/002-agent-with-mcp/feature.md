# 功能需求：Agent MCP工具调用系统

## 功能描述

实现一个自主决策的Agent系统，能够根据用户输入决定是否调用MCP工具。Agent支持多会话隔离，每个会话拥有独立的记忆空间，记忆全量保留所有对话历史和工具调用记录。

## 业务场景

用户通过WebSocket与Agent对话，Agent根据用户需求自动判断是否需要获取苹果数量或价格信息，并自主调用相应工具完成回答。

## 验收标准

### 1. Agent核心功能
- Agent能够根据用户输入自主决策是否调用工具
- 支持自然语言对话（如"苹果多少钱？"自动触发价格查询）
- 支持直接工具调用意图（如"获取苹果数量"）

### 2. MCP工具
- `get_apple_cnt`: 返回苹果数量（1、2、3随机数）
- `get_apple_price`: 返回苹果单价（10、20、40随机数）

### 3. 会话管理
- 不同`session_id`代表不同会话
- 每个会话拥有独立的记忆空间
- 记忆全量保留：system消息、user消息、assistant消息、tool调用参数和返回

### 4. WebSocket通信协议

#### 消息类型

**发送给客户端的消息：**

| 类型 | 描述 | 格式 |
|------|------|------|
| `received` | 收到前端消息确认 | `{"type": "received"}` |
| `msg_start` | 即将开始发送流式消息 | `{"type": "msg_start"}` |
| `msg_chunk` | AI文本流式响应块 | `{"type": "msg_chunk", "content": "..."}` |
| `msg_end` | AI文本响应结束 | `{"type": "msg_end"}` |
| `tool_start` | 开始工具调用 | `{"type": "tool_start", "tool_calls": [...]}` |
| `tool_end` | 工具调用结束 | `{"type": "tool_end", "results": [...]}` |
| `complete` | 一轮完整对话结束 | `{"type": "complete"}` |

#### 消息时序示例

**纯文本对话（无工具调用）：**
```
client → server: 发送消息
server → client: received
server → client: msg_start
server → client: msg_chunk (多次)
server → client: msg_end
server → client: complete
```

**带工具调用的对话：**
```
client → server: 发送消息
server → client: received
server → client: msg_start
server → client: msg_end (AI决定调用工具)
server → client: tool_start
server → client: tool_end (包含工具执行结果)
server → client: msg_start (AI根据工具结果回复)
server → client: msg_chunk (多次)
server → client: msg_end
server → client: complete
```

#### 流式处理规则
- `msg`类型的chunk：每收到一个立即通过ws发送
- `tool`类型的chunk：等待完整后拼接，一次性ws发送(tool_start)，然后调用MCP，把返回信息再通过ws发送(tool_end)，并返回给AI继续处理

### 5. 后端接口

```python
# 创建Agent实例
agent = create_agent(websocket)

# 发起对话
await agent.chat(message: str, session_id: str)
```

### 6. 技术要求
- 全异步实现（async/await）
- 不使用langgraph/langchain，基于openai和mcp原生实现
- 文件结构：
  - `agent.py` - Agent核心逻辑
  - `mcp/get_apple_cnt.py` - 获取苹果数量工具
  - `mcp/get_apple_price.py` - 获取苹果价格工具
  - `memory.py` - 记忆管理

## 非功能性需求

- 响应延迟：首包响应时间 < 2秒
- 支持标准的OpenAI兼容接口格式
- 工具调用链路完整可追溯
