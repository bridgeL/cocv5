# Agent HTTP 接口文档

本文档描述 Agent MCP工具调用系统 的 HTTP 接口规范。

---

## 接口概览

| 接口名 | 方法 | 地址 | 说明 |
|--------|------|------|------|
| 首页 | GET | / | 返回 Web 聊天界面 |

---

## 1. 首页

### 基本信息

- **接口地址**: `/`
- **请求方法**: GET
- **接口说明**: 返回 index.html 页面，提供 WebSocket 聊天界面

### 请求参数

无

### 正常返回

**返回格式**: HTML

```html
<!DOCTYPE html>
<html>
<head>...</head>
<body>...</body>
</html>
```

### 异常返回

| code | msg | 说明 |
|------|-----|------|
| - | index.html not found | 页面文件不存在 |

---

## 附：WebSocket 服务

Agent 核心功能通过 WebSocket 通信实现，详见 [docs/ws/agent.md](../ws/agent.md)。

- **WebSocket 地址**: `ws://localhost:8777`
- **通信格式**: JSON
