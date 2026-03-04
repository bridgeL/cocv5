# Agent WebSocket 通信协议文档

本文档描述 Agent MCP工具调用系统 的 WebSocket 通信协议规范。

---

## 连接信息

| 项目 | 值 |
|------|-----|
| WebSocket 地址 | `ws://localhost:8777` |
| 传输格式 | JSON |
| 心跳机制 | 客户端主动发送 ping，服务端回复 pong |

---

## 客户端发送消息

### 1. 心跳消息 (ping)

**用途**: 保持连接活跃，检测连接状态

**格式**:
```json
{
  "type": "ping",
  "time": 1234567890
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "ping" |
| time | number | 否 | 客户端时间戳 |

---

### 2. 回显消息 (echo)

**用途**: 测试连接，服务端原样返回

**格式**:
```json
{
  "type": "echo",
  "message": "测试消息"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "echo" |
| message | string | 是 | 要回显的内容 |

---

### 3. Agent 对话消息 (agent_chat)

**用途**: 与 Agent 进行对话，支持工具调用

**格式**:
```json
{
  "type": "agent_chat",
  "message": "苹果多少钱？",
  "session_id": "user_123"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定值 "agent_chat" |
| message | string | 是 | 用户消息内容 |
| session_id | string | 否 | 会话ID，不同ID代表不同会话，默认 "default" |

---

## 服务端发送消息

### 1. 心跳回复 (pong)

**触发条件**: 收到客户端 ping 消息

**格式**:
```json
{
  "type": "pong",
  "time": 1234567890,
  "server_time": 1234567891
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "pong" |
| time | number | 客户端传入的时间戳 |
| server_time | number | 服务端当前时间戳 |

---

### 2. 收到确认 (received)

**触发条件**: 收到客户端 agent_chat 消息

**格式**:
```json
{
  "type": "received"
}
```

---

### 3. 消息开始 (msg_start)

**触发条件**: AI 开始生成回复

**格式**:
```json
{
  "type": "msg_start"
}
```

---

### 4. 消息块 (msg_chunk)

**触发条件**: AI 流式生成文本内容

**格式**:
```json
{
  "type": "msg_chunk",
  "content": "苹果"
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "msg_chunk" |
| content | string | 文本内容片段 |

---

### 5. 消息结束 (msg_end)

**触发条件**: AI 文本生成结束

**格式**:
```json
{
  "type": "msg_end"
}
```

---

### 6. 工具调用开始 (tool_start)

**触发条件**: AI 决定调用工具

**格式**:
```json
{
  "type": "tool_start",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_apple_price",
        "arguments": "{}"
      }
    }
  ]
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "tool_start" |
| tool_calls | array | 工具调用列表 |
| tool_calls[].id | string | 工具调用唯一ID |
| tool_calls[].type | string | 固定值 "function" |
| tool_calls[].function.name | string | 工具名称 |
| tool_calls[].function.arguments | string | 工具参数（JSON字符串） |

**可用工具**:
| 工具名 | 说明 | 返回值 |
|--------|------|--------|
| get_apple_cnt | 获取苹果数量 | 1、2、3 随机整数 |
| get_apple_price | 获取苹果单价 | 10、20、40 随机整数 |

---

### 7. 工具调用结束 (tool_end)

**触发条件**: 工具执行完成

**格式**:
```json
{
  "type": "tool_end",
  "results": [
    {
      "tool_call_id": "call_abc123",
      "name": "get_apple_price",
      "result": "20",
      "status": "success"
    }
  ]
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "tool_end" |
| results | array | 工具执行结果列表 |
| results[].tool_call_id | string | 对应 tool_call 的 ID |
| results[].name | string | 工具名称 |
| results[].result | string | 工具返回结果（字符串） |
| results[].status | string | 执行状态："success" 或 "error" |

---

### 8. 对话完成 (complete)

**触发条件**: 一轮完整对话结束（包括工具调用后的最终回复）

**格式**:
```json
{
  "type": "complete"
}
```

---

### 9. 错误消息 (error)

**触发条件**: Agent 调用过程中发生错误

**格式**:
```json
{
  "type": "error",
  "error": "Agent 调用失败: ..."
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "error" |
| error | string | 错误描述 |

---

## 消息时序示例

### 纯文本对话（无工具调用）

```
client → server: {"type": "agent_chat", "message": "你好", "session_id": "user_123"}
server → client: {"type": "received"}
server → client: {"type": "msg_start"}
server → client: {"type": "msg_chunk", "content": "你"}
server → client: {"type": "msg_chunk", "content": "好"}
server → client: {"type": "msg_chunk", "content": "！"}
server → client: {"type": "msg_end"}
server → client: {"type": "complete"}
```

### 带工具调用的对话

```
client → server: {"type": "agent_chat", "message": "苹果多少钱？", "session_id": "user_123"}
server → client: {"type": "received"}
server → client: {"type": "msg_start"}
server → client: {"type": "msg_end"}                    <-- AI 决定调用工具，无文本内容
server → client: {"type": "tool_start", "tool_calls": [...]}
server → client: {"type": "tool_end", "results": [...]}  <-- 工具返回价格 20
server → client: {"type": "msg_start"}                   <-- AI 根据工具结果生成回复
server → client: {"type": "msg_chunk", "content": "苹果"}
server → client: {"type": "msg_chunk", "content": "20"}
server → client: {"type": "msg_chunk", "content": "元"}
server → client: {"type": "msg_end"}
server → client: {"type": "complete"}
```

---

## 会话管理

- **session_id** 用于隔离不同用户的对话历史
- 每个 session_id 拥有独立的记忆空间
- 记忆全量保留：system消息、user消息、assistant消息、tool调用记录
- 服务端重启后记忆丢失（当前为内存存储）
