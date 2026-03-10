import json
import sqlite3
from datetime import datetime
from typing import Any, Optional


class Memory:
    """内存类，存储对话历史到SQLite数据库"""

    def __init__(self, session_id: str, user_id: str | None = None, db_path: str = "memory.db"):
        self.session_id = session_id
        self.user_id = user_id
        self.db_path = db_path
        self._init_db()
        self._migrate_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    create_time TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def _migrate_db(self):
        """数据库迁移：添加 user_id 字段（如果不存在）"""
        with sqlite3.connect(self.db_path) as conn:
            # 检查 user_id 字段是否存在
            cursor = conn.execute("PRAGMA table_info(memory)")
            columns = [row[1] for row in cursor.fetchall()]
            if "user_id" not in columns:
                conn.execute("ALTER TABLE memory ADD COLUMN user_id TEXT")
                conn.commit()
                print("[DB] 迁移：添加 user_id 字段")

    def _insert_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[list[dict]] = None,
        tool_call_id: Optional[str] = None,
    ):
        """插入消息到数据库，实时保存"""
        create_time = int(datetime.now().timestamp() * 1000)
        tool_calls_json = (
            json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO memory (session_id, user_id, role, content, tool_calls, tool_call_id, create_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.session_id,
                    self.user_id,
                    role,
                    content,
                    tool_calls_json,
                    tool_call_id,
                    create_time,
                ),
            )
            conn.commit()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self._insert_message(role="user", content=content)

    def add_assistant_message(
        self, content: str, tool_calls: Optional[list[dict]] = None
    ):
        """添加助手消息"""
        self._insert_message(role="assistant", content=content, tool_calls=tool_calls)

    def add_tool_result(self, tool_call_id: str, content: str | dict):
        """添加工具执行结果，支持str或dict类型"""
        # 如果是dict，转换为JSON字符串
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = content
        self._insert_message(role="tool", content=content_str, tool_call_id=tool_call_id)

    def get_messages(self) -> list[dict[str, Any]]:
        """获取所有历史消息"""
        with sqlite3.connect(self.db_path) as conn:
            # 如果提供了 user_id，优先按 user_id 查询
            if self.user_id:
                cursor = conn.execute(
                    """
                    SELECT role, content, tool_calls, tool_call_id FROM memory
                    WHERE user_id = ?
                    ORDER BY id ASC
                    """,
                    (self.user_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT role, content, tool_calls, tool_call_id FROM memory
                    WHERE session_id = ?
                    ORDER BY id ASC
                    """,
                    (self.session_id,),
                )
            rows = cursor.fetchall()

        messages = []
        for role, content, tool_calls_json, tool_call_id in rows:
            msg: dict[str, Any] = {"role": role, "content": content}
            if tool_calls_json:
                msg["tool_calls"] = json.loads(tool_calls_json)
            if tool_call_id:
                msg["tool_call_id"] = tool_call_id
            messages.append(msg)
        return messages

    def clear(self):
        """清空当前session或用户的历史"""
        with sqlite3.connect(self.db_path) as conn:
            if self.user_id:
                conn.execute(
                    "DELETE FROM memory WHERE user_id = ?",
                    (self.user_id,),
                )
            else:
                conn.execute(
                    "DELETE FROM memory WHERE session_id = ?",
                    (self.session_id,),
                )
            conn.commit()
