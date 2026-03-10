import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser } from '../../../utils/user';
import { useWebSocket } from '../../../contexts/WebSocketContext';

export function useRoomChat(roomId) {
  const navigate = useNavigate();
  const { connectionStatus, send, onMessage } = useWebSocket();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [roomInfo, setRoomInfo] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState(null);
  const [isJoined, setIsJoined] = useState(false);

  // 气泡折叠状态
  const [collapseMode, setCollapseMode] = useState('all-expanded');
  const [collapsedItems, setCollapsedItems] = useState(new Set());

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const isAtBottomRef = useRef(true);

  const user = getUser();

  // 判断指定索引的气泡是否折叠
  const isCollapsed = useCallback((index, type) => {
    if (collapseMode === 'all-collapsed') {
      return type !== 'report';
    }
    if (collapseMode === 'all-expanded') return false;
    return collapsedItems.has(index);
  }, [collapseMode, collapsedItems]);

  // 切换单个气泡的折叠状态
  const toggleItemCollapse = useCallback((index) => {
    setCollapseMode('custom');
    setCollapsedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  }, []);

  // 注册WebSocket消息监听
  useEffect(() => {
    const unsubscribes = [];

    // 监听加入房间成功
    unsubscribes.push(onMessage('room_joined', (payload) => {
      setRoomInfo(payload.room);
      setMembers(payload.members || []);
      setIsJoined(true);
      // 加载历史消息
      send('load_room_history', { room_id: roomId, limit: 20 });
    }));

    // 监听房间消息
    unsubscribes.push(onMessage('room_message', (payload) => {
      setMessages(prev => [...prev, {
        type: 'user',
        userId: payload.user_id,
        nickname: payload.nickname,
        content: payload.content,
        isKP: payload.is_kp,
        isComplete: true
      }]);
    }));

    // 监听KP思考开始
    unsubscribes.push(onMessage('think_start', () => {
      setMessages(prev => [...prev, {
        type: 'think',
        nickname: 'KP',
        content: '',
        isKP: true,
        isComplete: false
      }]);
    }));

    // 监听KP流式输出
    unsubscribes.push(onMessage('think_chunk', (payload) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'think' && !lastMsg.isComplete) {
          return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + (payload.content || '') }];
        }
        return prev;
      });
    }));

    // 监听KP思考结束
    unsubscribes.push(onMessage('think_end', () => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'think') {
          return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
        }
        return prev;
      });
    }));

    // 监听KP回答开始
    unsubscribes.push(onMessage('report_start', () => {
      setMessages(prev => [...prev, {
        type: 'report',
        nickname: 'KP',
        content: '',
        isKP: true,
        isComplete: false
      }]);
    }));

    // 监听KP回答流式输出
    unsubscribes.push(onMessage('report_chunk', (payload) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'report' && !lastMsg.isComplete) {
          return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + (payload.content || '') }];
        }
        return prev;
      });
    }));

    // 监听KP回答结束
    unsubscribes.push(onMessage('report_end', () => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'report') {
          return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
        }
        return prev;
      });
    }));

    // 监听成员加入
    unsubscribes.push(onMessage('member_joined', (payload) => {
      if (payload.user_id !== user?.id) {
        setMembers(prev => [...prev, {
          user_id: payload.user_id,
          nickname: payload.nickname,
          is_owner: false
        }]);
      }
    }));

    // 监听成员离开
    unsubscribes.push(onMessage('member_left', (payload) => {
      setMembers(prev => prev.filter(m => m.user_id !== payload.user_id));
    }));

    // 监听历史消息
    unsubscribes.push(onMessage('room_history', (payload) => {
      if (payload.messages) {
        const formatted = payload.messages.map(msg => ({
          type: msg.role === 'assistant' ? (msg.think ? 'think' : 'report') : 'user',
          userId: msg.user_id,
          nickname: msg.role === 'assistant' ? 'KP' : (members.find(m => m.user_id === msg.user_id)?.nickname || msg.nickname || '未知'),
          content: msg.content,
          isKP: msg.role === 'assistant',
          isComplete: true
        }));
        setMessages(formatted);
      }
    }));

    // 监听房间关闭
    unsubscribes.push(onMessage('room_closed', () => {
      setError('房间已关闭');
      setTimeout(() => navigate('/rooms'), 2000);
    }));

    // 监听错误
    unsubscribes.push(onMessage('room_error', (payload) => {
      setError(payload.error);
      if (payload.error?.includes('不在该房间')) {
        setTimeout(() => navigate('/rooms'), 2000);
      }
    }));

    return () => unsubscribes.forEach(u => u());
  }, [onMessage, roomId, user?.id, members, navigate, send]);

  // 连接成功后加入房间
  useEffect(() => {
    if (connectionStatus === 'connected' && roomId) {
      send('join_room', { room_id: roomId });
    }
  }, [connectionStatus, roomId, send]);

  // 检查是否在底部
  const checkIsAtBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return true;
    return container.scrollHeight - container.scrollTop - container.clientHeight < 100;
  }, []);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (isAtBottomRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  // 监听滚动
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      isAtBottomRef.current = checkIsAtBottom();
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [checkIsAtBottom]);

  // 消息更新时滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 离开房间
  const leaveRoom = useCallback(() => {
    send('leave_room', { room_id: roomId });
    navigate('/rooms');
  }, [send, roomId, navigate]);

  // 发送消息
  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || !isJoined) return;

    setMessages(prev => [...prev, {
      type: 'user',
      userId: user?.id,
      nickname: user?.name || '我',
      content: text,
      isComplete: true
    }]);
    setInput('');
    isAtBottomRef.current = true;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

    send('room_chat', { room_id: roomId, content: text });
  }, [input, isJoined, roomId, send, user?.id, user?.name]);

  // 处理键盘事件
  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  // 设置折叠模式
  const setCollapseModeWithReset = useCallback((mode) => {
    setCollapseMode(mode);
    if (mode !== 'custom') {
      setCollapsedItems(new Set());
    }
  }, []);

  // 清除错误
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // 状态
    connectionStatus,
    messages,
    input,
    setInput,
    roomInfo,
    members,
    error,
    isJoined,
    collapseMode,

    // refs
    messagesEndRef,
    messagesContainerRef,

    // 方法
    isCollapsed,
    toggleItemCollapse,
    sendMessage,
    handleKeyPress,
    setCollapseMode: setCollapseModeWithReset,
    clearError,
    leaveRoom,
  };
}
