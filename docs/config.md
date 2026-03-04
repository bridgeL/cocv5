# 项目配置指南

## 环境安装

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

### 2. 激活虚拟环境

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 环境变量配置

项目使用 `.env` 文件管理配置。所有配置项均在 `.env` 文件中设置。

### 1. 创建配置文件

复制示例配置文件：

```bash
cp .env.example .env
```

### 2. 配置项说明

#### 模型配置 (必填)

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MODEL_NAME` | 模型名称 | `gpt-4o` |
| `MODEL_URL` | 模型API地址 | `https://api.openai.com/v1` |
| `MODEL_API_KEY` | API密钥 | `sk-xxxxxxxxxxxxxxxx` |
