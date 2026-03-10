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

            # 检查 room_id 字段是否存在
            if "room_id" not in columns:
                conn.execute("ALTER TABLE memory ADD COLUMN room_id TEXT")
                conn.commit()
                print("[DB] 迁移：添加 room_id 字段")

            # 创建 rooms 表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rooms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password TEXT,
                    owner_id TEXT NOT NULL,
                    kp_session_id TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # 创建 room_members 表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS room_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    UNIQUE(room_id, user_id)
                )
                """
            )
            conn.commit()
            print("[DB] 迁移：创建 rooms 和 room_members 表")

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

    def get_recent_rounds(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近 N 轮对话历史

        一轮 = 用户消息 + 后续AI响应（思考+工具+回答）
        策略：
        1. 查询最近 N 条用户消息的ID（倒序）
        2. 取最早的那条作为起始点
        3. 查询从该点之后的所有消息（正序）

        Args:
            limit: 轮数限制（默认20）

        Returns:
            消息列表，包含完整对话历史
        """
        if not self.user_id:
            return []

        with sqlite3.connect(self.db_path) as conn:
            # 获取最近 N 条用户消息的ID（倒序）
            cursor = conn.execute(
                """
                SELECT id FROM memory
                WHERE user_id = ? AND role = 'user'
                ORDER BY id DESC
                LIMIT ?
                """,
                (self.user_id, limit)
            )
            user_msg_ids = [row[0] for row in cursor.fetchall()]

            if not user_msg_ids:
                return []

            # 取最早的那条用户消息的id作为起始点
            min_id = min(user_msg_ids)

            # 查询从该点之后的所有消息（正序）
            cursor = conn.execute(
                """
                SELECT id, role, content, tool_calls, tool_call_id, create_time
                FROM memory
                WHERE user_id = ? AND id >= ?
                ORDER BY id ASC
                """,
                (self.user_id, min_id)
            )
            rows = cursor.fetchall()

        # 转换为字典列表
        messages = []
        for row in rows:
            msg: dict[str, Any] = {
                'id': row[0],
                'role': row[1],
                'content': row[2]
            }
            if row[3]:  # tool_calls
                msg["tool_calls"] = json.loads(row[3])
            if row[4]:  # tool_call_id
                msg["tool_call_id"] = row[4]
            if row[5]:  # create_time
                msg["create_time"] = row[5]
            messages.append(msg)

        return messages


class RoomMemory:
    """房间内存管理类，处理房间相关的数据库操作"""

    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path

    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def create_room(self, room_id: str, name: str, owner_id: str, password: str | None = None) -> dict:
        """创建房间"""
        now = str(int(datetime.now().timestamp() * 1000))
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO rooms (id, name, password, owner_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (room_id, name, password, owner_id, 'active', now, now)
            )
            conn.commit()
        return self.get_room(room_id)

    def get_room(self, room_id: str) -> dict | None:
        """获取房间信息"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, password, owner_id, kp_session_id, status, created_at, updated_at FROM rooms WHERE id = ?",
                (room_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'has_password': row[2] is not None,
                    'owner_id': row[3],
                    'kp_session_id': row[4],
                    'status': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None

    def set_kp_session(self, room_id: str, kp_session_id: str):
        """设置房间的KP session_id"""
        now = str(int(datetime.now().timestamp() * 1000))
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE rooms SET kp_session_id = ?, updated_at = ? WHERE id = ?",
                (kp_session_id, now, room_id)
            )
            conn.commit()

    def close_room(self, room_id: str, owner_id: str) -> bool:
        """关闭房间（仅房主可操作）"""
        now = str(int(datetime.now().timestamp() * 1000))
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE rooms SET status = 'closed', updated_at = ? WHERE id = ? AND owner_id = ?",
                (now, room_id, owner_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_rooms_by_owner(self, owner_id: str) -> list[dict]:
        """获取用户创建的房间列表"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT r.id, r.name, r.password, r.owner_id, r.status, r.created_at,
                       (SELECT COUNT(*) FROM room_members WHERE room_id = r.id) as member_count
                FROM rooms r
                WHERE r.owner_id = ? AND r.status = 'active'
                ORDER BY r.created_at DESC
                """,
                (owner_id,)
            )
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'has_password': row[2] is not None,
                    'owner_id': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'member_count': row[6]
                }
                for row in rows
            ]

    def list_rooms_by_member(self, user_id: str) -> list[dict]:
        """获取用户加入的房间列表（不包括自己创建的）"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT r.id, r.name, r.password, r.owner_id, r.status, r.created_at,
                       (SELECT COUNT(*) FROM room_members WHERE room_id = r.id) as member_count
                FROM rooms r
                JOIN room_members rm ON r.id = rm.room_id
                WHERE rm.user_id = ? AND r.owner_id != ? AND r.status = 'active'
                ORDER BY rm.joined_at DESC
                """,
                (user_id, user_id)
            )
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'has_password': row[2] is not None,
                    'owner_id': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'member_count': row[6]
                }
                for row in rows
            ]

    def list_public_rooms(self, exclude_user_id: str) -> list[dict]:
        """获取房间大厅（排除用户已加入的）"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT r.id, r.name, r.password, r.owner_id, r.status, r.created_at,
                       (SELECT COUNT(*) FROM room_members WHERE room_id = r.id) as member_count
                FROM rooms r
                WHERE r.status = 'active'
                AND r.id NOT IN (
                    SELECT room_id FROM room_members WHERE user_id = ?
                )
                AND r.owner_id != ?
                ORDER BY r.created_at DESC
                LIMIT 50
                """,
                (exclude_user_id, exclude_user_id)
            )
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'has_password': row[2] is not None,
                    'owner_id': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'member_count': row[6]
                }
                for row in rows
            ]

    def join_room(self, room_id: str, user_id: str, nickname: str) -> bool:
        """用户加入房间"""
        now = str(int(datetime.now().timestamp() * 1000))
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO room_members (room_id, user_id, nickname, joined_at) VALUES (?, ?, ?, ?)",
                    (room_id, user_id, nickname, now)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # 已经加入
            return False

    def leave_room(self, room_id: str, user_id: str) -> bool:
        """用户离开房间"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
                (room_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_room_members(self, room_id: str) -> list[dict]:
        """获取房间成员列表"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT rm.user_id, rm.nickname, rm.joined_at, r.owner_id
                FROM room_members rm
                JOIN rooms r ON rm.room_id = r.id
                WHERE rm.room_id = ?
                ORDER BY rm.joined_at ASC
                """,
                (room_id,)
            )
            rows = cursor.fetchall()
            return [
                {
                    'user_id': row[0],
                    'nickname': row[1],
                    'joined_at': row[2],
                    'is_owner': row[0] == row[3]
                }
                for row in rows
            ]

    def is_room_member(self, room_id: str, user_id: str) -> bool:
        """检查用户是否是房间成员"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM room_members WHERE room_id = ? AND user_id = ?",
                (room_id, user_id)
            )
            return cursor.fetchone() is not None

    def add_room_message(self, room_id: str, user_id: str | None, role: str, content: str,
                         tool_calls: list[dict] | None = None, tool_call_id: str | None = None):
        """添加房间消息"""
        create_time = str(int(datetime.now().timestamp() * 1000))
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memory (session_id, user_id, room_id, role, content, tool_calls, tool_call_id, create_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ('', user_id, room_id, role, content, tool_calls_json, tool_call_id, create_time)
            )
            conn.commit()

    def get_room_messages(self, room_id: str, limit: int = 20) -> list[dict]:
        """获取房间最近N轮对话历史"""
        with self._get_connection() as conn:
            # 获取最近N条用户消息的ID
            cursor = conn.execute(
                """
                SELECT id FROM memory
                WHERE room_id = ? AND role = 'user'
                ORDER BY id DESC
                LIMIT ?
                """,
                (room_id, limit)
            )
            user_msg_ids = [row[0] for row in cursor.fetchall()]

            if not user_msg_ids:
                return []

            min_id = min(user_msg_ids)

            # 查询从该点之后的所有消息
            cursor = conn.execute(
                """
                SELECT id, user_id, role, content, tool_calls, tool_call_id, create_time
                FROM memory
                WHERE room_id = ? AND id >= ?
                ORDER BY id ASC
                """,
                (room_id, min_id)
            )
            rows = cursor.fetchall()

        messages = []
        for row in rows:
            msg: dict[str, Any] = {
                'id': row[0],
                'user_id': row[1],
                'role': row[2],
                'content': row[3]
            }
            if row[4]:  # tool_calls
                msg["tool_calls"] = json.loads(row[4])
            if row[5]:  # tool_call_id
                msg["tool_call_id"] = row[5]
            if row[6]:  # create_time
                msg["create_time"] = row[6]
            messages.append(msg)

        return messages
