"""记忆管理模块 (SQLite 持久化存储)

按session_id隔离存储，全量保留所有对话历史和工具调用记录
"""

import json
import sqlite3
from typing import Any


class Memory:
    """记忆管理类 (SQLite 实现)

    每个session拥有独立的记忆空间，全量保留不做裁剪
    数据持久化到 SQLite 数据库
    """

    def __init__(self, db_path: str = "memory.db"):
        """
        Args:
            db_path: 数据库文件路径，默认项目根目录 memory.db
        """
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        cursor = self._conn.cursor()

        # 创建 messages 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_calls TEXT,
                tool_call_id TEXT,
                name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_role ON messages(session_id, role)
        """)

        self._conn.commit()

    def add_message(self, session_id: str, role: str, content: str | None = None, **kwargs) -> None:
        """添加消息到指定会话

        Args:
            session_id: 会话ID
            role: 角色 (system/user/assistant/tool)
            content: 消息内容
            **kwargs: 其他字段，如tool_calls、tool_call_id、name等
        """
        tool_calls = kwargs.get("tool_calls")
        tool_call_id = kwargs.get("tool_call_id")
        name = kwargs.get("name")

        # tool_calls 序列化为 JSON 字符串
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls is not None else None

        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, role, content, tool_calls_json, tool_call_id, name))
        self._conn.commit()

    def add_system_message(self, session_id: str, content: str) -> None:
        """添加系统消息"""
        self.add_message(session_id, "system", content)

    def add_user_message(self, session_id: str, content: str) -> None:
        """添加用户消息"""
        self.add_message(session_id, "user", content)

    def add_assistant_message(self, session_id: str, content: str | None = None, tool_calls: list[dict] | None = None) -> None:
        """添加助手消息

        Args:
            session_id: 会话ID
            content: 消息内容（可能为None当调用工具时）
            tool_calls: 工具调用请求
        """
        kwargs: dict[str, Any] = {}
        if tool_calls is not None:
            kwargs["tool_calls"] = tool_calls
        self.add_message(session_id, "assistant", content, **kwargs)

    def add_tool_result(self, session_id: str, tool_call_id: str, content: str, name: str | None = None) -> None:
        """添加工具调用结果

        Args:
            session_id: 会话ID
            tool_call_id: 工具调用ID
            content: 工具返回结果
            name: 工具名称
        """
        kwargs: dict[str, Any] = {"tool_call_id": tool_call_id}
        if name is not None:
            kwargs["name"] = name
        self.add_message(session_id, "tool", content, **kwargs)

    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """获取指定会话的完整对话历史

        Args:
            session_id: 会话ID

        Returns:
            该会话的所有消息列表（OpenAI 格式）
        """
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT role, content, tool_calls, tool_call_id, name
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))

        rows = cursor.fetchall()
        messages: list[dict[str, Any]] = []

        for row in rows:
            msg: dict[str, Any] = {"role": row["role"]}

            # content 可能为 None
            if row["content"] is not None:
                msg["content"] = row["content"]

            # 处理 assistant 的 tool_calls
            if row["tool_calls"] is not None:
                msg["tool_calls"] = json.loads(row["tool_calls"])

            # 处理 tool 角色的字段
            if row["tool_call_id"] is not None:
                msg["tool_call_id"] = row["tool_call_id"]
            if row["name"] is not None:
                msg["name"] = row["name"]

            messages.append(msg)

        return messages

    def clear_session(self, session_id: str) -> None:
        """清空指定会话的记忆

        Args:
            session_id: 会话ID
        """
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self._conn.commit()

    def has_session(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            会话是否存在
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT 1 FROM messages WHERE session_id = ? LIMIT 1",
            (session_id,)
        )
        return cursor.fetchone() is not None

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __del__(self):
        """析构时关闭连接"""
        if hasattr(self, '_conn') and self._conn:
            self._conn.close()


# 全局memory实例（单例）
_global_memory: Memory | None = None


def get_memory() -> Memory:
    """获取全局memory实例"""
    global _global_memory
    if _global_memory is None:
        _global_memory = Memory()
    return _global_memory
