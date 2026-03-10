# CoC V5 - AI 助手与克苏鲁的呼唤角色生成器

一个基于 React + FastAPI 的智能 AI 助手系统，支持多轮对话、工具调用、技能系统，并内置《克苏鲁的呼唤》第七版角色卡一键生成功能。

## 功能特性

### 核心功能
- **智能对话**：基于 OpenAI API 的流式对话，支持多轮上下文记忆
- **用户认证**：支持免登录模式和用户身份认证，历史消息按用户隔离
- **记忆系统**：SQLite 持久化存储，支持最近 20 轮历史消息加载
- **WebSocket 实时通信**：基于 WebSocket 的实时消息推送

### 工具系统 (Tools)
| 工具 | 描述 |
|------|------|
| `current_time` | 获取当前时间 |
| `weather` | 查询天气信息 |
| `roll_dice` | 掷骰子，支持复杂表达式（如 `3d6+2`） |
| `skill_check` | 技能检定，支持困难/极难成功判定 |
| `skill_manager` | 技能管理器，用于启用/禁用技能 |
| `coc_character_attributes` | CoC 7版角色属性一键生成 |

### 技能系统 (Skills)
| 技能 | 描述 |
|------|------|
| `WeatherAssistantSkill` | 天气助手技能 |
| `ReActSkill` | ReAct 推理技能 |
| `CoCCharacterGeneratorSkill` | CoC 7版角色卡生成技能 |
| `SkillLoaderSkill` | 技能加载管理技能 |

### CoC 角色生成器特色
严格按照《克苏鲁的呼唤》第七版规则书：
- **基础属性生成**：STR/CON/DEX/APP/POW（3d6 × 5）、SIZ/INT/EDU（(2d6+6) × 5）、Luck（3d6 × 5）
- **派生属性自动计算**：HP、MP、SAN、MOV、Build、DB
- **年龄调整逻辑**：支持教育增强检定和年龄减值
- **完整角色卡输出**：包含全额值/半值/五分之一值

## 技术栈

### 后端
- **Python 3.10+**
- **FastAPI** - Web 框架
- **WebSocket** - 实时通信
- **SQLite** - 数据持久化
- **OpenAI API** - LLM 接口

### 前端
- **React 19**
- **React Router 7** - 路由管理
- **Vite** - 构建工具
- **Lucide React** - 图标库

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 20+

## 项目结构

```
.
├── backend/                    # 后端代码
│   ├── app.py                 # FastAPI 应用入口
│   ├── agent.py               # Agent 核心逻辑
│   ├── memory.py              # 记忆/历史消息管理
│   ├── ws.py                  # WebSocket 连接管理
│   ├── llm_client.py          # LLM 客户端
│   ├── tool.py                # 工具基类
│   ├── skill.py               # 技能基类
│   ├── tools/                 # 工具实现
│   │   ├── current_time.py
│   │   ├── weather.py
│   │   ├── roll_dice.py
│   │   ├── skill_check.py
│   │   ├── skill_manager.py
│   │   └── coc_character_attributes.py
│   └── skills/                # 技能实现
│       ├── weather_assistant.py
│       ├── react_reasoning.py
│       ├── coc_character_generator.py
│       └── skill_loader.py
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── App.jsx            # 应用主组件
│   │   ├── components/
│   │   │   ├── Chat/          # 聊天组件
│   │   │   ├── Login/         # 登录组件
│   │   │   ├── ToolCall.jsx   # 工具调用展示
│   │   │   └── DictViewer.jsx # 字典查看器
│   │   └── utils/             # 工具函数
│   └── package.json
└── docs/                       # 项目文档
    └── dev/                    # 开发文档
        ├── start.md            # 启动指南
        ├── config.md           # 配置指南
        ├── git.md              # Git 规范
        └── workflow.md         # 开发流程
```

## 架构设计

### Agent 架构
- **Tools（工具）**: 可被 LLM 调用的功能单元，如掷骰子、查询天气
- **Skills（技能）**: Agent 的专业能力模块，通过提示词注入实现
- **Memory（记忆）**: 基于 SQLite 的对话历史存储，支持用户隔离
- **StreamBuffer（流式缓冲区）**: 处理 LLM 流式输出，支持 `<think>` 和 `<report>` 标签

### 通信协议
前后端通过 WebSocket 通信，支持以下消息类型：
- `agent_chat` - 用户发送消息
- `received` - 服务器确认接收
- `think_start/think_chunk/think_end` - 思考过程流式输出
- `report_start/report_chunk/report_end` - 正式回复流式输出
- `tool_before/tool_after` - 工具调用前后通知
- `complete` - 本轮对话结束

## 开发规范

- **Git 规范**: 见 [docs/dev/git.md](docs/dev/git.md)
- **开发流程**: 见 [docs/dev/workflow.md](docs/dev/workflow.md)
