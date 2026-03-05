// HTML 转义
export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 格式化值类型
export function formatValueType(value) {
  if (value === null) return '<span class="dict-value null">null</span>';
  if (typeof value === 'boolean') return `<span class="dict-value boolean">${value}</span>`;
  if (typeof value === 'number') return `<span class="dict-value number">${value}</span>`;
  if (typeof value === 'string') return `<span class="dict-value string">"${escapeHtml(value)}"</span>`;
  return `<span class="dict-value">${escapeHtml(String(value))}</span>`;
}

// 递归格式化字典/对象为美观的HTML
export function formatDict(data, level = 0, isRoot = true) {
  if (data === null || typeof data !== 'object') {
    return formatValueType(data);
  }

  const isArray = Array.isArray(data);
  const entries = isArray ? data : Object.entries(data);
  const isEmpty = isArray ? data.length === 0 : Object.keys(data).length === 0;

  if (isEmpty) {
    return `<span class="dict-value">${isArray ? '[]' : '{}'}</span>`;
  }

  let html = '';

  // 递归处理每个条目
  if (isArray) {
    entries.forEach((item, index) => {
      html += '<div class="dict-row">';
      html += `<span class="dict-key">[${index}]</span>`;
      if (item !== null && typeof item === 'object') {
        html += `<div class="dict-value nested">${formatDict(item, level + 1, false)}</div>`;
      } else {
        html += formatValueType(item);
      }
      html += '</div>';
    });
  } else {
    entries.forEach(([key, value]) => {
      html += '<div class="dict-row">';
      html += `<span class="dict-key">${escapeHtml(key)}</span>`;
      if (value !== null && typeof value === 'object') {
        html += `<div class="dict-value nested">${formatDict(value, level + 1, false)}</div>`;
      } else {
        html += formatValueType(value);
      }
      html += '</div>';
    });
  }

  if (isRoot) {
    return `<div class="dict-container">${html}</div>`;
  }
  return html;
}

// 简化版字典展示（用于紧凑显示）
export function formatDictCompact(data) {
  if (data === null || typeof data !== 'object') {
    return String(data);
  }
  const entries = Object.entries(data);
  if (entries.length === 0) return '{}';

  const preview = entries.slice(0, 3).map(([k, v]) => {
    let val = v;
    if (v !== null && typeof v === 'object') val = '{...}';
    else if (typeof v === 'string') val = `"${v.substring(0, 20)}${v.length > 20 ? '...' : ''}"`;
    return `${k}: ${val}`;
  }).join(', ');

  return entries.length > 3 ? `{${preview}, ...}` : `{${preview}}`;
}
