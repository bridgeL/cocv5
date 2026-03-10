/**
 * 房间相关工具函数
 */

/**
 * 生成房间ID
 * 格式: rm_ + 12位随机字符
 * @returns {string} 房间ID
 */
export function generateRoomId() {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = 'rm_';
  for (let i = 0; i < 12; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * 格式化时间戳为友好显示
 * @param {string|number} timestamp - 时间戳（毫秒）
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(timestamp) {
  if (!timestamp) return '';

  const date = new Date(parseInt(timestamp));
  const now = new Date();
  const diff = now - date;

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚';
  }

  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`;
  }

  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`;
  }

  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`;
  }

  // 其他情况显示日期
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 房间状态映射
 */
export const ROOM_STATUS = {
  active: '进行中',
  closed: '已关闭'
};

/**
 * Tab标签映射
 */
export const ROOM_TABS = {
  created: {
    key: 'created',
    label: '我创建的',
    description: '你作为房主创建的房间'
  },
  joined: {
    key: 'joined',
    label: '我加入的',
    description: '你作为玩家加入的房间'
  },
  hall: {
    key: 'hall',
    label: '房间大厅',
    description: '所有公开的房间'
  }
};
