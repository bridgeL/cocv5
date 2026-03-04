# Memory 数据库表结构文档

本文档描述 Agent MCP工具调用系统 的 SQLite 数据库存储结构。

---

## 表概览

| 表名 | 说明 | 数据量预估 |
|------|------|-----------|
| messages | 存储所有对话消息 | 随会话数增长 |

---

## 1. messages 表

### 表说明

存储所有会话的消息记录，按 session_id 隔离，一条记录代表一条消息。

### 表结构

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键，唯一标识每条消息 |
| session_id | TEXT | NOT NULL | 会话ID，用于区分不同会话 |
| role | TEXT | NOT NULL | 消息角色：system/user/assistant/tool |
| content | TEXT | 可空 | 消息内容，assistant调用工具时可能为NULL |
| tool_calls | TEXT | 可空 | 工具调用请求，JSON字符串格式，assistant角色特有 |
| tool_call_id | TEXT | 可空 | 工具调用唯一ID，tool角色必填 |
| name | TEXT | 可空 | 工具名称，tool角色必填 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 消息创建时间 |

### 索引

| 索引名 | 字段 | 说明 |
|--------|------|------|
| idx_session_id | session_id | 加速按会话查询 |
| idx_session_role | session_id, role | 加速按会话和角色筛选 |

### 建表 SQL

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_calls TEXT,
    tool_call_id TEXT,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_session_role ON messages(session_id, role);
```

### 数据示例

**system 消息：**
| id | session_id | role | content | tool_calls | tool_call_id | name | created_at |
|----|------------|------|---------|------------|--------------|------|------------|
| 1 | user_123 | system | 你是助手... | NULL | NULL | NULL | 2025-03-02 10:00:00 |

**user 消息：**
| id | session_id | role | content | tool_calls | tool_call_id | name | created_at |
|----|------------|------|---------|------------|--------------|------|------------|
| 2 | user_123 | user | 苹果多少钱？ | NULL | NULL | NULL | 2025-03-02 10:00:05 |

**assistant 消息（调用工具）：**
| id | session_id | role | content | tool_calls | tool_call_id | name | created_at |
|----|------------|------|---------|------------|--------------|------|------------|
| 3 | user_123 | assistant | NULL | [{"id":"call_abc","function":{"name":"get_apple_price"}}] | NULL | NULL | 2025-03-02 10:00:06 |

**tool 消息：**
| id | session_id | role | content | tool_calls | tool_call_id | name | created_at |
|----|------------|------|---------|------------|--------------|------|------------|
| 4 | user_123 | tool | 20 | NULL | call_abc | get_apple_price | 2025-03-02 10:00:07 |

---

## 设计说明

### 为什么不用外键

根据项目规范，所有数据表只允许有主键约束，不允许有任何外键。原因：
1. 简化数据模型，提高插入性能
2. 业务逻辑层控制数据一致性
3. 便于后续分库分表扩展

### 字段设计考量

1. **session_id 使用 TEXT**：支持任意字符串格式的会话ID
2. **content 可空**：assistant 调用工具时 content 为 NULL
3. **tool_calls 存储为 JSON 字符串**：SQLite 无原生数组类型，JSON 字符串足够表达复杂结构
4. **created_at 自动设置**：记录消息时序，便于排序和追溯

### 存储位置

数据库文件位于项目根目录：`memory.db`
