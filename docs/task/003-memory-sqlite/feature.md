# 功能需求：Memory SQLite 持久化存储

## 功能描述

将现有的内存存储（`memory.py`）改造为 SQLite 数据库持久化存储，实现会话数据的持久化保留。每条消息作为数据库中的一行记录存储，支持 system、user、assistant、tool 四种类型的消息。

## 业务场景

当前系统使用内存字典存储对话历史，服务端重启后所有会话数据丢失。通过改造为 SQLite 存储，实现：
- 服务端重启后会话数据不丢失
- 支持长期对话历史保留
- 为后续数据分析和会话管理提供基础

## 验收标准

### 1. 数据库表结构

**表名**: `messages`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 自增主键 |
| session_id | TEXT NOT NULL | 会话ID，用于隔离不同会话 |
| role | TEXT NOT NULL | 消息角色：system/user/assistant/tool |
| content | TEXT | 消息内容（可能为NULL，如tool_calls时） |
| tool_calls | TEXT | 工具调用请求（JSON字符串，assistant角色时可能有） |
| tool_call_id | TEXT | 工具调用ID（tool角色时必填） |
| name | TEXT | 工具名称（tool角色时必填） |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_session_id` ON `session_id` - 加速会话查询
- `idx_session_role` ON `session_id`, `role` - 加速按角色筛选

### 2. Memory 类改造要求

**保持接口不变**，内部实现改为 SQLite 操作：

```python
# 以下方法保持原有签名和行为
- add_message(session_id, role, content=None, **kwargs)
- add_system_message(session_id, content)
- add_user_message(session_id, content)
- add_assistant_message(session_id, content=None, tool_calls=None)
- add_tool_result(session_id, tool_call_id, content, name=None)
- get_messages(session_id) -> list[dict]
- clear_session(session_id)
- has_session(session_id) -> bool
```

**新增方法**:
```python
- close()  # 关闭数据库连接
```

### 3. 数据持久化要求

- 数据库文件存储在项目根目录：`memory.db`
- 表结构在首次初始化时自动创建
- 所有写操作立即提交（事务保证）
- 读取操作返回 OpenAI 格式的消息列表（与现有格式一致）

### 4. 消息存储格式

**system 消息**:
```json
{"role": "system", "content": "系统提示词"}
```

**user 消息**:
```json
{"role": "user", "content": "用户消息"}
```

**assistant 消息（纯文本）**:
```json
{"role": "assistant", "content": "AI回复"}
```

**assistant 消息（调用工具）**:
```json
{"role": "assistant", "content": null, "tool_calls": [...]}
```

**tool 消息**:
```json
{"role": "tool", "tool_call_id": "call_xxx", "name": "tool_name", "content": "结果"}
```

### 5. 性能要求

- 单条消息写入 < 10ms
- 查询单会话全部消息 < 50ms（1000条以内）

### 6. 兼容性要求

- `get_memory()` 仍返回单例 Memory 实例
- 不改动 `agent.py` 的任何调用代码
- 不改动现有 WebSocket 协议

## 非功能性需求

- 使用 Python 标准库 `sqlite3`
- 线程安全（支持多并发访问）
- 优雅处理数据库异常，不影响主流程
- 提供数据库连接关闭机制
