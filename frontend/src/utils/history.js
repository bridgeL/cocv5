/**
 * 历史消息解析工具
 * 将后端存储格式转换为前端展示格式
 */

/**
 * 解析AI消息中的 think/report 标签
 * @param {string} content
 * @returns {{think: string, report: string}}
 */
export function parseThinkReport(content) {
  // 提取所有 think 标签内容（可能有多个）
  const thinkMatches = [...content.matchAll(/<think>([\s\S]*?)<\/think>/g)];
  const think = thinkMatches.map(m => m[1].trim()).join('\n\n');

  // 提取 report 标签内容
  const reportMatch = content.match(/<report>([\s\S]*?)<\/report>/);
  let report = '';

  if (reportMatch) {
    // 如果有 report 标签，使用标签内的内容，并移除其中的 think 标签
    report = reportMatch[1].trim();
    // 移除 report 中可能嵌套的 think 标签及其内容
    report = report.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
  } else if (!think) {
    // 如果没有 think 也没有 report 标签，整个内容作为 report
    report = content.trim();
  }

  return { think, report };
}

/**
 * 将后端历史消息转换为前端消息格式
 * @param {Array} historyMessages - 后端返回的消息列表
 * @returns {Array} 前端格式的消息列表
 */
export function convertHistoryToFrontend(historyMessages) {
  const result = [];
  const toolResults = {}; // tool_call_id -> result

  // 第一遍：收集所有 tool 结果
  historyMessages.forEach(msg => {
    if (msg.role === 'tool' && msg.tool_call_id) {
      toolResults[msg.tool_call_id] = msg.content;
    }
  });

  // 第二遍：构建前端消息
  historyMessages.forEach(msg => {
    switch (msg.role) {
      case 'user':
        result.push({
          type: 'user',
          content: msg.content,
          isComplete: true
        });
        break;

      case 'assistant':
        // 解析 think 和 report
        const { think, report } = parseThinkReport(msg.content);

        if (think) {
          result.push({
            type: 'think',
            content: think,
            isComplete: true
          });
        }

        // 处理 tool_calls
        if (msg.tool_calls) {
          msg.tool_calls.forEach(tc => {
            // 处理不同格式的 tool_call
            const toolId = tc.id;
            const toolName = tc.function?.name || tc.name;
            const toolArgs = tc.function?.arguments || tc.arguments || '{}';

            result.push({
              type: 'tool',
              id: toolId,
              name: toolName,
              args: typeof toolArgs === 'string' ? JSON.parse(toolArgs) : toolArgs,
              result: toolResults[toolId],
              status: toolResults[toolId] ? 'success' : 'executing'
            });
          });
        }

        if (report) {
          result.push({
            type: 'report',
            content: report,
            isComplete: true
          });
        }
        break;

      case 'tool':
        // tool 消息已在 assistant 处理时关联，跳过
        break;
    }
  });

  return result;
}
