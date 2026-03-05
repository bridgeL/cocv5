import DictViewer from './DictViewer';
import './ToolCall.css';

export default function ToolCall({ name, args, result, status }) {
  // 解析参数和结果
  let parsedArgs = args;
  if (typeof args === 'string') {
    try { parsedArgs = JSON.parse(args); } catch(e) {}
  }

  let parsedResult = result;
  if (typeof result === 'string') {
    try { parsedResult = JSON.parse(result); } catch(e) {}
  }

  // 检查是否有错误
  const hasError = parsedResult && typeof parsedResult === 'object' && parsedResult.error;

  // 确定状态
  const isExecuting = status === 'executing';
  const isSuccess = status === 'success' && !hasError;
  const isError = status === 'error' || hasError;

  // 样式类
  const className = `tool-call ${isExecuting ? 'executing' : ''} ${isSuccess ? 'success' : ''} ${isError ? 'error' : ''}`;

  // 图标和标题
  let icon = '⚙️';
  let title = `正在调用: ${name}`;
  if (isSuccess) {
    icon = '✓';
    title = `${name} 执行完成`;
  } else if (isError) {
    icon = '❌';
    title = `${name} 执行失败`;
  }

  return (
    <div className={className}>
      <div className="tool-call-header">
        <span className="tool-call-icon">{icon}</span>
        <span>{title}</span>
      </div>

      <div className="tool-call-section">
        <div className="tool-call-section-title">输入参数</div>
        <DictViewer data={parsedArgs} />
      </div>

      {result !== undefined && (
        <div className="tool-call-section">
          <div className="tool-call-section-title">{hasError ? '错误信息' : '返回结果'}</div>
          <DictViewer data={parsedResult} />
        </div>
      )}
    </div>
  );
}
