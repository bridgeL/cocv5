# 项目配置指南

## 后端

### 安装

python 3.10

```bash
# 创建虚拟环境
cd backend
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

项目使用 `.env` 文件管理配置。所有配置项均在 `.env` 文件中设置。

复制示例配置文件：

```bash
cp .env.example .env
```

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MODEL_NAME` | 模型名称 | `gpt-4o` |
| `MODEL_URL` | 模型API地址 | `https://api.openai.com/v1` |
| `MODEL_API_KEY` | API密钥 | `sk-xxxxxxxxxxxxxxxx` |

## 前端

node 20

```bash
cd frontend
npm install
npm run dev
```
