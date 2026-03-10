/**
 * 用户身份管理工具
 * 实现免登录机制：自动生成用户ID，存储在 localStorage
 */

const USER_STORAGE_KEY = 'coc_user';

/**
 * 生成安全的随机ID
 * @param {number} length - ID长度
 * @returns {string} 随机字符串
 */
export function generateSecureId(length = 12) {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, b => b.toString(36).padStart(2, '0')).join('').slice(0, length);
}

/**
 * 生成用户ID
 * @returns {string} 用户ID (格式: ub_xxxxxxxxxxxx)
 */
export function generateUserId() {
  return 'ub_' + generateSecureId(12);
}

/**
 * 生成Token
 * @returns {string} 32位随机Token
 */
export function generateToken() {
  return generateSecureId(32);
}

/**
 * 形容词列表
 */
const ADJECTIVES = [
  '勇敢的', '机智的', '神秘的', '冷静的', '热情的',
  '好奇的', '谨慎的', '果断的', '优雅的', '坚毅的',
  '敏锐的', '沉着的', '博学的', '风趣的', '温柔的'
];

/**
 * 名词列表
 */
const NOUNS = [
  '调查员', '冒险者', '探险家', '旅行者', '守护者',
  '学者', '侦探', '骑士', '行者', '观察者',
  '猎手', '引路人', '追寻者', '守望者', '漫游者'
];

/**
 * 生成随机昵称
 * @returns {string} 随机昵称 (例: 勇敢的调查员#0423)
 */
export function generateRandomNickname() {
  const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)];
  const num = Math.floor(Math.random() * 9999);
  return `${adj}${noun}#${num.toString().padStart(4, '0')}`;
}

/**
 * 创建新用户
 * @param {string} nickname - 用户昵称（可选，默认随机生成）
 * @returns {Object} 用户对象
 */
export function createUser(nickname = null) {
  const user = {
    id: generateUserId(),
    token: generateToken(),
    nickname: nickname || generateRandomNickname(),
    createdAt: Date.now()
  };
  saveUser(user);
  return user;
}

/**
 * 保存用户到 localStorage
 * @param {Object} user - 用户对象
 */
export function saveUser(user) {
  try {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  } catch (e) {
    console.error('Failed to save user:', e);
  }
}

/**
 * 从 localStorage 获取用户
 * @returns {Object|null} 用户对象或 null
 */
export function getUser() {
  try {
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to parse user:', e);
    // 解析失败时清除损坏的数据
    clearUser();
  }
  return null;
}

/**
 * 检查用户是否已存在
 * @returns {boolean}
 */
export function hasUser() {
  return getUser() !== null;
}

/**
 * 清除用户数据
 */
export function clearUser() {
  try {
    localStorage.removeItem(USER_STORAGE_KEY);
  } catch (e) {
    console.error('Failed to clear user:', e);
  }
}

/**
 * 更新用户昵称
 * @param {string} newNickname - 新昵称
 * @returns {Object|null} 更新后的用户对象
 */
export function updateNickname(newNickname) {
  const user = getUser();
  if (user) {
    user.nickname = newNickname.trim() || user.nickname;
    saveUser(user);
    return user;
  }
  return null;
}

/**
 * 用户对象结构
 * @typedef {Object} User
 * @property {string} id - 用户唯一标识 (ub_xxxxxxxxxxxx)
 * @property {string} token - 身份令牌
 * @property {string} nickname - 用户昵称
 * @property {number} createdAt - 创建时间戳
 */
