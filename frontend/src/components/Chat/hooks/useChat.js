import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useWebSocket } from '../../../contexts/WebSocketContext';

export function useChat() {
  const { connectionStatus, isAuthenticated, send, onMessage } = useWebSocket();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isReceivingReport, setIsReceivingReport] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentToolCall, setCurrentToolCall] = useState(null);
  const [error, setError] = useState(null);

  // 气泡折叠状态
  const [collapseMode, setCollapseMode] = useState('all-expanded');
  const [collapsedItems, setCollapsedItems] = useState(new Set());

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const isAtBottomRef = useRef(true);
  const placeholderThinkRef = useRef(null);

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

  // 简略模式下是否需要显示占位思考气泡
  // 只要还在处理中，且不在接收报告状态，就显示占位思考气泡
  const showPlaceholderThink = useMemo(() => {
    return isProcessing && !isReceivingReport;
  }, [isProcessing, isReceivingReport]);

  // 注册WebSocket消息监听
  useEffect(() => {
    const unsubscribes = [];

    unsubscribes.push(onMessage('session_init', (payload) => {
      setSessionId(payload.session_id);
      setError(null);
    }));

    unsubscribes.push(onMessage('history_messages', (payload) => {
      if (payload.messages?.length > 0) {
        const formatted = [];
        payload.messages.forEach(msg => {
          if (msg.role === 'user') {
            formatted.push({ type: 'user', content: msg.content, isComplete: true });
          } else if (msg.role === 'assistant') {
            if (msg.think) {
              formatted.push({ type: 'think', content: msg.think, isComplete: true });
            }
            if (msg.tool_calls) {
              msg.tool_calls.forEach(tc => {
                formatted.push({
                  type: 'tool',
                  id: tc.id,
                  name: tc.name,
                  args: typeof tc.arguments === 'string' ? JSON.parse(tc.arguments) : tc.arguments,
                  result: tc.result,
                  status: tc.result ? 'success' : 'executing'
                });
              });
            }
            if (msg.report) {
              formatted.push({ type: 'report', content: msg.report, isComplete: true });
            }
          }
        });
        setMessages(formatted);
      }
    }));

    unsubscribes.push(onMessage('user_auth_failed', (payload) => {
      setError('用户认证失败: ' + (payload.error || '未知错误'));
    }));

    unsubscribes.push(onMessage('received', () => {
      setIsProcessing(true);
      setIsReceivingReport(false);
      setMessages(prev => {
        const hasThink = prev.some(m => m.type === 'think' && !m.isComplete);
        const hasExecutingTool = prev.some(m => m.type === 'tool' && m.status === 'executing');
        if (!hasThink && !hasExecutingTool) {
          const placeholderId = `think-${Date.now()}`;
          placeholderThinkRef.current = placeholderId;
          return [...prev, { type: 'think', content: '', isComplete: false, isPlaceholder: true, id: placeholderId }];
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('think_start', () => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'think' && lastMsg.isPlaceholder) {
          placeholderThinkRef.current = null;
          return [...prev.slice(0, -1), { type: 'think', content: '', isComplete: false }];
        }
        return [...prev, { type: 'think', content: '', isComplete: false }];
      });
    }));

    unsubscribes.push(onMessage('think_chunk', (payload) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'think' && !lastMsg.isComplete) {
          return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + payload.content }];
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('think_end', () => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'think') {
          return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('report_start', () => {
      setIsReceivingReport(true);
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'think' && lastMsg.isPlaceholder) {
          placeholderThinkRef.current = null;
          return [...prev.slice(0, -1), { type: 'report', content: '', isComplete: false }];
        }
        return [...prev, { type: 'report', content: '', isComplete: false }];
      });
    }));

    unsubscribes.push(onMessage('report_chunk', (payload) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'report' && !lastMsg.isComplete) {
          return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + payload.content }];
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('report_end', () => {
      setIsReceivingReport(false);
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'report') {
          return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('tool_before', (payload) => {
      if (payload.tool_calls) {
        payload.tool_calls.forEach(tc => {
          setCurrentToolCall({ id: tc.id, name: tc.name, args: tc.arguments, status: 'executing' });
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            const newTool = { type: 'tool', id: tc.id, name: tc.name, args: tc.arguments, status: 'executing' };
            if (lastMsg?.type === 'think' && lastMsg.isPlaceholder) {
              placeholderThinkRef.current = null;
              return [...prev.slice(0, -1), newTool];
            }
            return [...prev, newTool];
          });
        });
      }
    }));

    unsubscribes.push(onMessage('tool_after', (payload) => {
      if (payload.results) {
        payload.results.forEach(result => {
          setCurrentToolCall(null);
          setMessages(prev => {
            const targetIndex = prev.findIndex(m => m.type === 'tool' && m.id === result.id && m.status === 'executing');
            if (targetIndex !== -1) {
              const updated = [...prev];
              updated[targetIndex] = { ...updated[targetIndex], result: result.result, status: 'success' };
              return updated;
            }
            return prev;
          });
        });
      }
    }));

    unsubscribes.push(onMessage('complete', () => {
      setIsProcessing(false);
      setIsReceivingReport(false);
      placeholderThinkRef.current = null;
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'assistant') {
          return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
        }
        if (lastMsg?.type === 'think' && lastMsg.isPlaceholder) {
          return prev.slice(0, -1);
        }
        return prev;
      });
      setCurrentToolCall(null);
    }));

    unsubscribes.push(onMessage('error', (payload) => {
      setIsProcessing(false);
      setIsReceivingReport(false);
      placeholderThinkRef.current = null;
      setError(payload.error || '未知错误');
      setCurrentToolCall(null);
    }));

    return () => unsubscribes.forEach(u => u());
  }, [onMessage]);

  // 认证成功后加载历史
  useEffect(() => {
    if (isAuthenticated) {
      send('load_history', { limit: 20 });
    }
  }, [isAuthenticated, send]);

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
      const currentScrollTop = container.scrollTop;
      isAtBottomRef.current = checkIsAtBottom();
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [checkIsAtBottom]);

  // 消息更新时滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 发送消息
  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || isProcessing) return;

    setMessages(prev => [...prev, { type: 'user', content: text }]);
    setInput('');
    isAtBottomRef.current = true;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

    send('agent_chat', { message: text });
  }, [input, isProcessing, send]);

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
    isProcessing,
    sessionId,
    error,
    collapseMode,
    showPlaceholderThink,

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
  };
}
