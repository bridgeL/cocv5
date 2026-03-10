import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { User } from 'lucide-react';
import ToolCall from '../ToolCall';
import { getUser } from '../../utils/user';
import './Chat.css';

export default function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentToolCall, setCurrentToolCall] = useState(null);
  const [error, setError] = useState(null);
  // 占位思考气泡的ID
  const placeholderThinkRef = useRef(null);

  // 气泡折叠状态：'all-collapsed' | 'custom' | 'all-expanded'
  const [collapseMode, setCollapseMode] = useState('all-expanded');
  // 单个气泡的折叠状态，key 为消息索引
  const [collapsedItems, setCollapsedItems] = useState(new Set());

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const currentAssistantMsgRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const isAtBottomRef = useRef(true);
  const lastScrollTopRef = useRef(0);

  // 当前流式消息的状态
  const streamStateRef = useRef({
    type: null, // 'think' | 'report' | 'normal'
    messageId: null
  });

  // 判断指定索引的气泡是否折叠
  const isCollapsed = useCallback((index, type) => {
    if (collapseMode === 'all-collapsed') {
      // 简略模式：思考折叠，回答展开，工具折叠
      if (type === 'report') return false;
      return true;
    }
    if (collapseMode === 'all-expanded') return false;
    // custom 模式
    return collapsedItems.has(index);
  }, [collapseMode, collapsedItems]);

  // 切换单个气泡的折叠状态
  const toggleItemCollapse = useCallback((index) => {
    setCollapseMode('custom');
    setCollapsedItems(prev => {
      // 根据当前模式初始化 collapsedItems
      let newSet;
      if (collapseMode === 'all-collapsed') {
        // 从简略模式进入自定义：保持简略模式的默认状态，然后翻转点击的
        // 简略模式：思考折叠(true)，回答展开(false)，工具折叠(true)
        newSet = new Set();
        messages.forEach((msg, i) => {
          if (msg.type === 'report') {
            // 回答默认展开，不需要加入 collapsedItems
          } else {
            // 思考和工具默认折叠
            newSet.add(i);
          }
        });
        // 翻转点击的气泡状态
        if (newSet.has(index)) {
          newSet.delete(index);
        } else {
          newSet.add(index);
        }
      } else if (collapseMode === 'all-expanded') {
        // 从详细模式进入自定义：所有都展开，然后折叠点击的
        newSet = new Set();
        newSet.add(index);
      } else {
        // 已经在自定义模式，正常切换
        newSet = new Set(prev);
        if (newSet.has(index)) {
          newSet.delete(index);
        } else {
          newSet.add(index);
        }
      }
      return newSet;
    });
  }, [collapseMode, messages]);

  // 切换全局折叠模式
  const toggleCollapseMode = useCallback(() => {
    setCollapseMode(prev => {
      if (prev === 'all-collapsed') return 'all-expanded';
      if (prev === 'all-expanded') return 'all-collapsed';
      // 从 custom 切换到 all-expanded
      return 'all-expanded';
    });
    // 切换全局模式时清空自定义状态
    setCollapsedItems(new Set());
  }, []);

  // 检查是否在底部（距离底部 100px 以内认为是在底部）
  const checkIsAtBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return true;
    const threshold = 100;
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  }, []);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (isAtBottomRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  // 监听滚动事件，根据滚动方向和位置判断是否进入智能滚动
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const currentScrollTop = container.scrollTop;
      const scrollDirection = currentScrollTop > lastScrollTopRef.current ? 'down' : 'up';
      lastScrollTopRef.current = currentScrollTop;

      const atBottom = checkIsAtBottom();

      if (scrollDirection === 'up') {
        // 向上滚动：退出智能滚动
        isAtBottomRef.current = false;
      } else {
        // 向下滚动：根据位置判断是否进入智能滚动
        isAtBottomRef.current = atBottom;
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [checkIsAtBottom]);

  // 消息更新时，如果在底部则自动滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // WebSocket 连接
  useEffect(() => {
    let isConnecting = false;
    let reconnectTimer = null;

    const connect = () => {
      if (isConnecting || wsRef.current?.readyState === WebSocket.OPEN) return;
      isConnecting = true;

      // 直连后端 WebSocket，不经过 Vite 代理
      const wsUrl = 'ws://127.0.0.1:8080/ws';

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnecting = false;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WS Receive]', data.type, data);
          handleMessage(data);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        isConnecting = false;
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('连接出错');
        isConnecting = false;
      };
    };

    const handleMessage = (data) => {
      switch (data.type) {
        case 'session_init':
          setSessionId(data.session_id);
          setError(null);
          // 发送用户认证信息
          const user = getUser();
          if (user && wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'user_auth',
              user_id: user.id,
              nickname: user.nickname
            }));
            console.log('[WS Send] user_auth:', { user_id: user.id, nickname: user.nickname });
          }
          break;

        case 'user_auth_success':
          console.log('[WS] 用户认证成功:', data);
          setIsConnected(true);
          // 认证成功后加载历史消息
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'load_history',
              limit: 20
            }));
            console.log('[WS Send] load_history: { limit: 20 }');
          }
          break;

        case 'history_messages':
          // 结构化历史消息，已切分 think 和 report
          console.log('[WS] 收到历史消息:', data.messages?.length || 0, '条');
          if (data.messages && data.messages.length > 0) {
            const formatted = [];
            data.messages.forEach(msg => {
              if (msg.role === 'user') {
                formatted.push({ type: 'user', content: msg.content, isComplete: true });
              } else if (msg.role === 'assistant') {
                // think 部分
                if (msg.think) {
                  formatted.push({ type: 'think', content: msg.think, isComplete: true });
                }
                // tool_calls
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
                // report 部分
                if (msg.report) {
                  formatted.push({ type: 'report', content: msg.report, isComplete: true });
                }
              }
            });
            setMessages(formatted);
          }
          break;

        case 'user_auth_failed':
          console.error('[WS] 用户认证失败:', data);
          setError('用户认证失败: ' + (data.error || '未知错误'));
          break;

        case 'received':
          setIsProcessing(true);
          // 添加占位思考气泡（如果没有真正的思考气泡，也没有正在执行的工具调用）
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
          break;

        case 'chunk':
          // 普通流式输出
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            // 如果有占位思考气泡，替换成普通助手消息
            if (lastMsg && lastMsg.type === 'think' && lastMsg.isPlaceholder) {
              placeholderThinkRef.current = null;
              return [...prev.slice(0, -1), { type: 'assistant', content: data.content, isComplete: false }];
            }
            if (lastMsg && lastMsg.type === 'assistant' && !lastMsg.isComplete) {
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content }
              ];
            }
            return [...prev, { type: 'assistant', content: data.content, isComplete: false }];
          });
          break;

        case 'think_start':
          // 思考开始
          streamStateRef.current.type = 'think';
          setMessages(prev => {
            // 如果有占位思考气泡，替换它
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'think' && lastMsg.isPlaceholder) {
              placeholderThinkRef.current = null;
              return [...prev.slice(0, -1), { type: 'think', content: '', isComplete: false }];
            }
            return [...prev, { type: 'think', content: '', isComplete: false }];
          });
          break;

        case 'think_chunk':
          // 思考内容
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'think' && !lastMsg.isComplete) {
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content }
              ];
            }
            return [...prev, { type: 'think', content: data.content, isComplete: false }];
          });
          break;

        case 'think_end':
          // 思考结束
          streamStateRef.current.type = null;
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'think') {
              return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
            }
            return prev;
          });
          break;

        case 'report_start':
          // 汇报开始
          streamStateRef.current.type = 'report';
          setMessages(prev => {
            // 如果有占位思考气泡，替换它
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'think' && lastMsg.isPlaceholder) {
              placeholderThinkRef.current = null;
              return [...prev.slice(0, -1), { type: 'report', content: '', isComplete: false }];
            }
            return [...prev, { type: 'report', content: '', isComplete: false }];
          });
          break;

        case 'report_chunk':
          // 汇报内容
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'report' && !lastMsg.isComplete) {
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content }
              ];
            }
            return [...prev, { type: 'report', content: data.content, isComplete: false }];
          });
          break;

        case 'report_end':
          // 汇报结束
          streamStateRef.current.type = null;
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'report') {
              return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
            }
            return prev;
          });
          break;

        case 'tool_before':
          // 工具调用前
          if (data.tool_calls) {
            data.tool_calls.forEach(tc => {
              setCurrentToolCall({
                id: tc.id,
                name: tc.name,
                args: tc.arguments,
                status: 'executing'
              });
              setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                const newTool = {
                  type: 'tool',
                  id: tc.id,  // 保存 tool call id 用于后续匹配
                  name: tc.name,
                  args: tc.arguments,
                  status: 'executing'
                };
                // 如果有占位思考气泡，移除它（工具调用气泡已有思考中标签）
                if (lastMsg && lastMsg.type === 'think' && lastMsg.isPlaceholder) {
                  placeholderThinkRef.current = null;
                  return [...prev.slice(0, -1), newTool];
                }
                return [...prev, newTool];
              });
            });
          }
          break;

        case 'tool_after':
          // 工具调用后
          if (data.results) {
            data.results.forEach(result => {
              setCurrentToolCall(null);
              setMessages(prev => {
                // 根据 id 找到对应的 tool 消息
                const targetIndex = prev.findIndex(
                  m => m.type === 'tool' && m.id === result.id && m.status === 'executing'
                );
                if (targetIndex !== -1) {
                  const updatedMessages = [...prev];
                  updatedMessages[targetIndex] = {
                    ...updatedMessages[targetIndex],
                    result: result.result,
                    status: 'success'
                  };
                  return updatedMessages;
                }
                return prev;
              });
            });
          }
          break;

        case 'complete':
          setIsProcessing(false);
          placeholderThinkRef.current = null;
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'assistant') {
              return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
            }
            // 如果最后一个是占位思考气泡，移除它
            if (lastMsg && lastMsg.type === 'think' && lastMsg.isPlaceholder) {
              return prev.slice(0, -1);
            }
            return prev;
          });
          setCurrentToolCall(null);
          break;

        case 'error':
          setIsProcessing(false);
          placeholderThinkRef.current = null;
          setError(data.error || '未知错误');
          setCurrentToolCall(null);
          break;
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  // 发送消息
  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || isProcessing || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    setMessages(prev => [...prev, { type: 'user', content: text }]);
    setInput('');

    // 发送消息后立刻滚动到底部
    isAtBottomRef.current = true;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

    const msg = { type: 'agent_chat', message: text };
    console.log('[WS Send]', msg);
    wsRef.current.send(JSON.stringify(msg));
  }, [input, isProcessing]);

  // 处理键盘事件
  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  return (
    <div className="chat-container">
      {/* 顶部状态栏 */}
      <header className="chat-header">
        <div className="header-left">
          <h1>AI 助手</h1>
          <div className="status">
            <span className={`status-dot ${isConnected ? 'connected' : ''}`}></span>
            <span>{isConnected ? '已连接' : '连接中...'}</span>
          </div>
        </div>
        <div className="header-right">
          {/* 用户入口 */}
          <button
            className="user-menu-button"
            onClick={() => navigate('/user')}
            title="个人中心"
          >
            <User size={18} />
          </button>
          {/* 气泡折叠开关 */}
          <div className="collapse-toggle" title="折叠/展开气泡">
            <button
              className={collapseMode === 'all-collapsed' ? 'active' : ''}
              onClick={() => { setCollapseMode('all-collapsed'); setCollapsedItems(new Set()); }}
            >
              简略
            </button>
            <button
              className={collapseMode === 'custom' ? 'active' : ''}
              onClick={() => {
                if (collapseMode === 'all-collapsed') {
                  // 从简略模式切换到自定义：保持简略模式的默认状态
                  const newSet = new Set();
                  messages.forEach((msg, i) => {
                    if (msg.type !== 'report') {
                      newSet.add(i);
                    }
                  });
                  setCollapsedItems(newSet);
                } else if (collapseMode === 'all-expanded') {
                  // 从详细模式切换到自定义：所有都展开
                  setCollapsedItems(new Set());
                }
                setCollapseMode('custom');
              }}
            >
              自定义
            </button>
            <button
              className={collapseMode === 'all-expanded' ? 'active' : ''}
              onClick={() => { setCollapseMode('all-expanded'); setCollapsedItems(new Set()); }}
            >
              详细
            </button>
          </div>
          {sessionId && <div className="session-id">Session: {sessionId}</div>}
        </div>
      </header>

      {/* 消息区域 */}
      <div className="messages" ref={messagesContainerRef}>
        {messages.map((msg, index) => {
          if (msg.type === 'user') {
            return (
              <div key={index} className="message user">
                <div className="message-header">你</div>
                <div className="message-content">{msg.content}</div>
              </div>
            );
          }

          if (msg.type === 'think') {
            const collapsed = isCollapsed(index, 'think');
            const isPlaceholder = msg.isPlaceholder;
            const isStreaming = !msg.isComplete;
            return (
              <div
                key={index}
                className={`message think ${collapsed ? 'collapsed' : ''} ${isPlaceholder ? 'placeholder' : ''}`}
              >
                <div
                  className="message-header"
                  onClick={() => toggleItemCollapse(index)}
                  title={collapsed ? '点击展开' : '点击折叠'}
                  style={{ cursor: 'pointer' }}
                >
                  {isPlaceholder ? (
                    <span className="tool-call-thinking">思考中...</span>
                  ) : (
                    <>
                      思考
                      {isStreaming && <span className="tool-call-thinking">思考中...</span>}
                    </>
                  )}
                  {!isPlaceholder && (collapsed ? ' ▶' : ' ▼')}
                </div>
                {!collapsed && !isPlaceholder && (
                  <div className="message-content">
                    {msg.content}
                  </div>
                )}
              </div>
            );
          }

          if (msg.type === 'report') {
            const collapsed = isCollapsed(index, 'report');
            const isStreaming = !msg.isComplete;
            return (
              <div key={index} className={`message report ${collapsed ? 'collapsed' : ''}`}>
                <div
                  className="message-header"
                  onClick={() => toggleItemCollapse(index)}
                  title={collapsed ? '点击展开' : '点击折叠'}
                  style={{ cursor: 'pointer' }}
                >
                  回答
                  {isStreaming && <span className="tool-call-thinking">回答中...</span>}
                  {collapsed ? ' ▶' : ' ▼'}
                </div>
                {!collapsed && (
                  <div className="message-content">{msg.content}</div>
                )}
              </div>
            );
          }

          if (msg.type === 'tool') {
            return (
              <ToolCall
                key={index}
                name={msg.name}
                args={msg.args}
                result={msg.result}
                status={msg.status}
                collapsed={isCollapsed(index, 'tool')}
                onToggle={() => toggleItemCollapse(index)}
              />
            );
          }

          return null;
        })}

        {/* 上一个气泡已完成，但还在等待下一个气泡开始时显示占位思考气泡 */}
        {isProcessing &&
          messages.length > 0 &&
          (() => {
            const lastMsg = messages[messages.length - 1];
            // 检查最后一个消息是否已完成
            if (lastMsg.type === 'tool') {
              return lastMsg.status !== 'executing';
            }
            return lastMsg.isComplete;
          })() && (
          <div className="message think placeholder">
            <div className="message-header">
              <span className="tool-call-thinking">思考中...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="input-area">
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息..."
            disabled={!isConnected}
            autoComplete="off"
          />
          <button onClick={sendMessage} disabled={!isConnected}>
            发送
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className={`error-toast ${error ? 'show' : ''}`} onAnimationEnd={() => setError(null)}>
          {error}
        </div>
      )}
    </div>
  );
}
