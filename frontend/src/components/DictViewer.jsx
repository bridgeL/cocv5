import './DictViewer.css';

// 格式化值类型
function formatValueType(value) {
  if (value === null) return <span className="dict-value null">null</span>;
  if (typeof value === 'boolean') return <span className="dict-value boolean">{String(value)}</span>;
  if (typeof value === 'number') return <span className="dict-value number">{value}</span>;
  if (typeof value === 'string') return <span className="dict-value string">"{value}"</span>;
  return <span className="dict-value">{String(value)}</span>;
}

// 字典行组件
function DictRow({ itemKey, value, isArray }) {
  const isObject = value !== null && typeof value === 'object';

  return (
    <div className="dict-row">
      <span className="dict-key">{isArray ? `[${itemKey}]` : itemKey}</span>
      {isObject ? (
        <div className="dict-value nested">
          <DictViewer data={value} isRoot={false} />
        </div>
      ) : (
        formatValueType(value)
      )}
    </div>
  );
}

// 字典查看器组件
export default function DictViewer({ data, isRoot = true }) {
  if (data === null || typeof data !== 'object') {
    return formatValueType(data);
  }

  const isArray = Array.isArray(data);
  const entries = isArray ? data : Object.entries(data);
  const isEmpty = isArray ? data.length === 0 : Object.keys(data).length === 0;

  if (isEmpty) {
    return <span className="dict-value">{isArray ? '[]' : '{}'}</span>;
  }

  const content = isArray
    ? entries.map((item, index) => (
        <DictRow key={index} itemKey={index} value={item} isArray={true} />
      ))
    : entries.map(([key, value]) => (
        <DictRow key={key} itemKey={key} value={value} isArray={false} />
      ));

  if (isRoot) {
    return <div className="dict-container">{content}</div>;
  }

  return <>{content}</>;
}
