# Agent WebSocket 文档

本文档描述 AI Agent 系统的 WebSocket 消息格式。

---

## 连接信息

- **连接地址**: `ws://{host}:8080/ws`
- **协议**: WebSocket
- **编码**: JSON

---

## 客户端 → 服务端 消息

### 1. ping

心跳检测消息。

#### 消息格式

```json
{
  "type": "ping",
  "time": 1234567890
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 消息类型，固定为 `ping` |
| time | number | 否 | 客户端发送时间戳 |

---

### 2. echo

回显测试消息，服务端原样返回。

#### 消息格式

```json
{
  "type": "echo",
  "message": "测试消息"
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 消息类型，固定为 `echo` |
| message | string | 是 | 需要回显的内容 |

---

### 3. agent_chat

与 AI Agent 对话（主要功能）。

#### 消息格式

```json
{
  "type": "agent_chat",
  "message": "你好，今天天气怎么样？"
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 消息类型，固定为 `agent_chat` |
| message | string | 是 | 用户输入的消息内容 |

---

### 4. chat（已弃用）

旧版对话消息，已弃用，请使用 `agent_chat`。

#### 消息格式

```json
{
  "type": "chat",
  "message": "消息内容"
}
```

#### 响应

返回 `chat_error` 消息，提示使用新版接口。

---

## 服务端 → 客户端 消息

### 1. session_init

连接建立后，服务端发送 session 初始化信息。

#### 消息格式

```json
{
  "type": "session_init",
  "session_id": "a1b2c3d4"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `session_init` |
| session_id | string | 唯一会话标识符（8位字符串） |

---

### 2. pong

心跳响应。

#### 消息格式

```json
{
  "type": "pong",
  "time": 1234567890,
  "server_time": 1234567891
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `pong` |
| time | number | 客户端发送的原始时间戳 |
| server_time | number | 服务端当前时间戳 |

---

### 3. echo

回显响应。

#### 消息格式

```json
{
  "type": "echo",
  "message": "测试消息",
  "timestamp": 1234567890
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `echo` |
| message | string | 原样返回的消息内容 |
| timestamp | number | 服务端处理时间戳 |

---

### 4. received

表示已接收到用户的 agent_chat 消息，本轮对话开始。

#### 消息格式

```json
{
  "type": "received",
  "message": "你好，今天天气怎么样？"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `received` |
| message | string | 用户输入的消息内容 |

---

### 5. chunk

LLM 流式响应分片。

#### 消息格式

```json
{
  "type": "chunk",
  "content": "这是一段"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `chunk` |
| content | string | 当前流式分片内容 |

---

### 6. tool_before

Agent 开始调用工具。

#### 消息格式

```json
{
  "type": "tool_before",
  "tool_calls": [
    {
      "id": "call_abc123",
      "name": "weather",
      "arguments": "{\"city\": \"北京\"}"
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `tool_before` |
| tool_calls | array | 工具调用列表 |
| tool_calls[].id | string | 工具调用唯一标识 |
| tool_calls[].name | string | 工具名称 |
| tool_calls[].arguments | string | 工具参数（JSON字符串） |

---

### 7. tool_after

工具执行完成。

#### 消息格式

```json
{
  "type": "tool_after",
  "results": [
    {
      "id": "call_abc123",
      "name": "weather",
      "result": {
        "city": "北京",
        "temperature": 22,
        "condition": "晴",
        "humidity": 45,
        "wind": "北风3级"
      }
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `tool_after` |
| results | array | 工具执行结果列表 |
| results[].id | string | 工具调用标识 |
| results[].name | string | 工具名称 |
| results[].result | object | 工具返回结果（字典类型） |

---

### 8. complete

本轮对话完成。

#### 消息格式

```json
{
  "type": "complete",
  "response": "北京今天天气晴朗，温度22°C，湿度45%，北风3级。"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `complete` |
| response | string | 完整的助手回复内容 |

---

### 9. chat_error

旧版 chat 接口错误提示。

#### 消息格式

```json
{
  "type": "chat_error",
  "error": "请使用 agent_chat 消息类型"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `chat_error` |
| error | string | 错误提示信息 |

---

### 10. error

通用错误消息。

#### 消息格式

```json
{
  "type": "error",
  "error": "错误描述信息"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `error` |
| error | string | 错误描述 |

---

### 11. unknown

未知消息类型响应。

#### 消息格式

```json
{
  "type": "unknown",
  "received": {
    "type": "some_unknown_type"
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 `unknown` |
| received | object | 原样返回接收到的消息内容 |

---

## 典型对话流程

```
客户端                           服务端
  |                                |
  |-------- WebSocket 连接 ------->|
  |<------- session_init --------|
  |                                |
  |-------- agent_chat ---------->|
  |<--------- received ----------|
  |<---------- chunk ------------|
  |<---------- chunk ------------|
  |<-------- tool_before --------|
  |<-------- tool_after ---------|
  |<---------- chunk ------------|
  |<---------- chunk ------------|
  |<--------- complete ----------|
  |                                |
  |-------- agent_chat ---------->|
  |           ...                  |
```
