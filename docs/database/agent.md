# Agent 数据库文档

本文档描述 AI Agent 系统的数据表设计。

---

## 数据表列表

### 1. memory

存储对话历史记录。

#### 表名

`memory`

#### 字段定义

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键，唯一标识每条记录 |
| session_id | TEXT | NOT NULL | 会话标识符，关联同一对话会话 |
| role | TEXT | NOT NULL | 消息角色：`user` / `assistant` / `tool` |
| content | TEXT | NOT NULL | 消息内容文本 |
| tool_calls | TEXT | NULL | 工具调用信息（JSON字符串），仅 assistant 角色使用 |
| tool_call_id | TEXT | NULL | 工具调用标识，仅 tool 角色使用 |
| create_time | TEXT | NOT NULL | 消息创建时间戳（毫秒级整数） |

#### 字段详细说明

**id**
- 类型：INTEGER
- 自增主键，自动生成
- 用于排序和唯一标识

**session_id**
- 类型：TEXT
- 不可为空
- 每个 WebSocket 连接生成唯一的 8 位 session_id
- 用于隔离不同用户的对话历史

**role**
- 类型：TEXT
- 取值范围：
  - `user`: 用户发送的消息
  - `assistant`: AI 助手发送的消息
  - `tool`: 工具执行结果

**content**
- 类型：TEXT
- 消息的实际内容
- 对于 tool 角色，存储工具返回的 JSON 字符串

**tool_calls**
- 类型：TEXT（JSON字符串）
- 可选字段
- 当 assistant 调用工具时，存储工具调用信息
- 格式示例：
```json
[
  {
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "weather",
      "arguments": "{\"city\": \"北京\"}"
    }
  }
]
```

**tool_call_id**
- 类型：TEXT
- 可选字段
- 仅 `tool` 角色使用，关联对应的工具调用
- 与 tool_calls 中的 id 对应

**create_time**
- 类型：TEXT（存储毫秒级时间戳）
- 不可为空
- 记录创建时间，用于按时间排序

#### 索引建议

```sql
-- 按 session_id 查询历史记录（常用查询）
CREATE INDEX idx_memory_session_id ON memory(session_id);

-- 按创建时间排序
CREATE INDEX idx_memory_create_time ON memory(create_time);
```

#### 典型查询示例

```sql
-- 查询指定会话的所有消息
SELECT role, content, tool_calls, tool_call_id
FROM memory
WHERE session_id = ?
ORDER BY id ASC;

-- 清空指定会话的历史
DELETE FROM memory
WHERE session_id = ?;

-- 查询会话数量统计
SELECT session_id, COUNT(*) as msg_count
FROM memory
GROUP BY session_id;
```

---

## 数据库设计规范

### 约束原则

1. **只允许有主键约束**，不允许有任何外键
2. 所有表必须包含自增主键 `id`
3. 时间字段使用毫秒级时间戳存储
4. JSON 数据以 TEXT 类型存储

### 数据类型选择

| 数据类型 | 用途 |
|----------|------|
| INTEGER | 整数、布尔值、自增ID |
| TEXT | 字符串、JSON、日期时间 |
| REAL | 浮点数 |
| BLOB | 二进制数据 |

### 命名规范

- 表名：小写字母，下划线分隔
- 字段名：小写字母，下划线分隔
- 主键名：统一为 `id`
