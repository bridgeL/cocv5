"""
房间管理模块
处理房间生命周期、成员管理、消息广播
"""

import uuid
import hashlib
from typing import Optional
from memory import RoomMemory


class RoomManager:
    """房间管理器，管理所有房间的状态和操作"""

    def __init__(self, db_path: str = "memory.db"):
        self.room_memory = RoomMemory(db_path)
        # 存储活跃房间的用户连接 {room_id: {user_id: WebSocketConnection}}
        self.active_rooms: dict[str, dict[str, any]] = {}
        # 存储用户的房间归属 {user_id: room_id}
        self.user_rooms: dict[str, str] = {}

    def generate_room_id(self) -> str:
        """生成房间ID: rm_ + 12位随机字符"""
        return "rm_" + str(uuid.uuid4())[:12].replace("-", "")

    def _hash_password(self, password: str) -> str:
        """使用SHA256哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    async def create_room(self, name: str, owner_id: str, nickname: str, password: Optional[str] = None, ws_connection=None) -> dict:
        """
        创建房间

        Args:
            name: 房间名称
            owner_id: 创建者用户ID
            nickname: 创建者昵称
            password: 房间密码（可选）
            ws_connection: 创建者的WebSocket连接

        Returns:
            房间信息字典
        """
        room_id = self.generate_room_id()
        hashed_password = self._hash_password(password) if password else None

        # 创建房间记录
        room = self.room_memory.create_room(room_id, name, owner_id, hashed_password)

        # 房主自动加入房间
        self.room_memory.join_room(room_id, owner_id, nickname)

        # 如果提供了连接，将房主加入活跃房间
        if ws_connection:
            if room_id not in self.active_rooms:
                self.active_rooms[room_id] = {}
            self.active_rooms[room_id][owner_id] = ws_connection
            self.user_rooms[owner_id] = room_id

        print(f"[Room] 创建房间: {room_id} ({name}) by {nickname} ({owner_id})")
        return room

    async def join_room(self, room_id: str, user_id: str, nickname: str, password: Optional[str] = None, ws_connection=None) -> dict:
        """
        加入房间

        Args:
            room_id: 房间ID
            user_id: 用户ID
            nickname: 用户昵称
            password: 房间密码（如果需要）
            ws_connection: 用户的WebSocket连接

        Returns:
            包含room和members的字典，或抛出异常
        """
        # 获取房间信息
        room = self.room_memory.get_room(room_id)
        if not room:
            raise ValueError("房间不存在")

        if room['status'] != 'active':
            raise ValueError("房间已关闭")

        # 检查密码
        if room['has_password']:
            if not password:
                raise ValueError("需要密码")
            hashed_input = self._hash_password(password)
            # 需要从数据库获取原始密码进行比对
            import sqlite3
            with sqlite3.connect(self.room_memory.db_path) as conn:
                cursor = conn.execute(
                    "SELECT password FROM rooms WHERE id = ?",
                    (room_id,)
                )
                row = cursor.fetchone()
                if row and row[0] and row[0] != hashed_input:
                    raise ValueError("密码错误")

        # 检查是否已经在房间中
        if self.room_memory.is_room_member(room_id, user_id):
            # 已经在房间中，只是更新连接
            if ws_connection:
                if room_id not in self.active_rooms:
                    self.active_rooms[room_id] = {}
                self.active_rooms[room_id][user_id] = ws_connection
                self.user_rooms[user_id] = room_id
        else:
            # 加入房间
            success = self.room_memory.join_room(room_id, user_id, nickname)
            if not success:
                raise ValueError("加入房间失败")

            # 添加到活跃房间
            if ws_connection:
                if room_id not in self.active_rooms:
                    self.active_rooms[room_id] = {}
                self.active_rooms[room_id][user_id] = ws_connection
                self.user_rooms[user_id] = room_id

            # 广播新成员加入消息
            await self.broadcast_to_room(room_id, "member_joined", {
                "room_id": room_id,
                "user_id": user_id,
                "nickname": nickname
            }, exclude_user=user_id)

        print(f"[Room] 用户加入房间: {nickname} ({user_id}) -> {room_id}")

        # 返回房间信息和成员列表
        members = self.room_memory.get_room_members(room_id)
        return {
            "room": room,
            "members": members
        }

    async def leave_room(self, room_id: str, user_id: str) -> bool:
        """
        离开房间

        Args:
            room_id: 房间ID
            user_id: 用户ID

        Returns:
            是否成功离开
        """
        # 从数据库中移除
        success = self.room_memory.leave_room(room_id, user_id)

        # 从活跃房间中移除
        if room_id in self.active_rooms and user_id in self.active_rooms[room_id]:
            del self.active_rooms[room_id][user_id]
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

        # 从用户房间映射中移除
        if user_id in self.user_rooms:
            del self.user_rooms[user_id]

        if success:
            # 广播成员离开消息
            await self.broadcast_to_room(room_id, "member_left", {
                "room_id": room_id,
                "user_id": user_id
            })
            print(f"[Room] 用户离开房间: {user_id} -> {room_id}")

        return success

    async def close_room(self, room_id: str, owner_id: str) -> bool:
        """
        关闭房间（仅房主可操作）

        Args:
            room_id: 房间ID
            owner_id: 房主用户ID

        Returns:
            是否成功关闭
        """
        # 关闭房间
        success = self.room_memory.close_room(room_id, owner_id)

        if success:
            # 广播房间关闭消息
            await self.broadcast_to_room(room_id, "room_closed", {
                "room_id": room_id
            })

            # 清理活跃房间中的所有成员
            if room_id in self.active_rooms:
                for user_id in list(self.active_rooms[room_id].keys()):
                    if user_id in self.user_rooms:
                        del self.user_rooms[user_id]
                del self.active_rooms[room_id]

            print(f"[Room] 房间关闭: {room_id}")

        return success

    def get_room_list(self, user_id: str, tab: str) -> list[dict]:
        """
        获取房间列表

        Args:
            user_id: 用户ID
            tab: 标签类型 ('created', 'joined', 'hall')

        Returns:
            房间列表
        """
        if tab == 'created':
            return self.room_memory.list_rooms_by_owner(user_id)
        elif tab == 'joined':
            return self.room_memory.list_rooms_by_member(user_id)
        elif tab == 'hall':
            return self.room_memory.list_public_rooms(user_id)
        else:
            return []

    async def broadcast_to_room(self, room_id: str, msg_type: str, data: dict, exclude_user: Optional[str] = None):
        """
        广播消息给房间所有成员

        Args:
            room_id: 房间ID
            msg_type: 消息类型
            data: 消息数据
            exclude_user: 排除的用户ID（可选）
        """
        if room_id not in self.active_rooms:
            return

        for user_id, connection in self.active_rooms[room_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await connection.send(msg_type, data)
            except Exception as e:
                print(f"[!] 广播消息失败: {user_id} - {e}")

    async def send_to_user(self, room_id: str, user_id: str, msg_type: str, data: dict):
        """
        发送消息给指定用户

        Args:
            room_id: 房间ID
            user_id: 用户ID
            msg_type: 消息类型
            data: 消息数据
        """
        if room_id not in self.active_rooms:
            return

        connection = self.active_rooms[room_id].get(user_id)
        if connection:
            try:
                await connection.send(msg_type, data)
            except Exception as e:
                print(f"[!] 发送消息失败: {user_id} - {e}")

    def get_room_members(self, room_id: str) -> list[dict]:
        """获取房间成员列表"""
        return self.room_memory.get_room_members(room_id)

    def is_user_in_room(self, user_id: str, room_id: str) -> bool:
        """检查用户是否在房间中"""
        return self.room_memory.is_room_member(room_id, user_id)

    def get_user_room(self, user_id: str) -> Optional[str]:
        """获取用户当前所在的房间ID"""
        return self.user_rooms.get(user_id)

    def add_message(self, room_id: str, user_id: Optional[str], role: str, content: str, **kwargs):
        """添加房间消息到数据库"""
        self.room_memory.add_room_message(room_id, user_id, role, content, **kwargs)

    def get_room_messages(self, room_id: str, limit: int = 20) -> list[dict]:
        """获取房间历史消息"""
        return self.room_memory.get_room_messages(room_id, limit)


# 全局房间管理器实例
room_manager = RoomManager()
