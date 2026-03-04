# 任务计划：Memory SQLite 持久化存储

## 任务拆解

### 任务1：数据库表设计文档
**文件：** `docs/database/memory.md`

**步骤：**
1. 定义 messages 表结构
2. 定义索引
3. 说明字段含义和约束

**验收标准：**
- 文档符合项目规范
- 字段类型和约束明确

---

### 任务2：Memory 类 SQLite 改造
**文件：** `memory.py`（完全重写）

**步骤：**
1. 导入 sqlite3 模块
2. 改造 `__init__` 方法：
   - 创建数据库连接
   - 创建 messages 表（如果不存在）
   - 创建索引
3. 实现 `_init_db()` 私有方法初始化表结构
4. 改造 `add_message()` 方法：
   - 将消息插入数据库
   - 处理 tool_calls 序列化为 JSON
5. 改造 `add_system_message()`：调用 add_message
6. 改造 `add_user_message()`：调用 add_message
7. 改造 `add_assistant_message()`：
   - 处理 content 可能为 None
   - tool_calls 序列化为 JSON 字符串存储
8. 改造 `add_tool_result()`：
   - 存储 tool_call_id 和 name
9. 改造 `get_messages()`：
   - 按 session_id 查询所有消息
   - 按 created_at 排序
   - 反序列化 tool_calls
   - 返回 OpenAI 格式列表
10. 改造 `clear_session()`：
    - 删除该 session_id 的所有记录
11. 改造 `has_session()`：
    - 查询该 session_id 是否存在记录
12. 新增 `close()` 方法：关闭数据库连接

**验收标准：**
- 所有原有方法接口保持不变
- 数据持久化到 SQLite
- 单测通过

---

### 任务3：集成测试
**文件：** 修改 `app.py`（可选，添加优雅关闭）

**步骤：**
1. 在应用退出时调用 memory.close()
2. 验证重启后数据不丢失

**验收标准：**
- 服务端重启后会话数据保留
- 正常对话流程无异常

---

### 任务4：功能验证

**步骤：**
1. 自测：创建会话、添加消息、查询消息
2. 自测：重启服务后数据是否保留
3. 自测：多会话隔离是否正常
4. 自测：工具调用链路是否正常

**验收标准：**
- 所有功能按 feature.md 验收标准通过

---

## 开发顺序

1. 任务1 → 任务2 → 任务3 → 任务4

## 风险点

- 需要确保与现有 Memory 类接口 100% 兼容
- tool_calls 的 JSON 序列化/反序列化要处理正确
- 数据库连接的生命周期管理
