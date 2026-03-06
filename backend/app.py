import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ws import handle_websocket


# 创建 FastAPI 应用
app = FastAPI(title="WebSocket Demo HTTP Server")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """返回 index.html 页面"""
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接处理器
    - 每个连接生成独立的 session_id
    - 创建独立的 Memory 和 Agent
    - 处理 ping/pong 心跳
    - 处理 Agent 对话
    """
    await handle_websocket(websocket)


async def main():
    """主函数 - 启动 HTTP + WebSocket 服务 (统一端口 8080)"""
    print("🚀 服务器启动中...")
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
