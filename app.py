import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

from agent import create_agent


# 创建 FastAPI 应用
app = FastAPI(title="WebSocket Demo HTTP Server")


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
    - 处理 ping/pong 心跳（前端主动 ping）
    - 处理消息回显
    - 处理 Agent 对话
    """
    await websocket.accept()
    client = f"{websocket.client.host}:{websocket.client.port}"
    print(f"[+] WebSocket 客户端连接: {client}")

    # 创建 Agent 实例（每个连接一个）
    agent = create_agent(websocket)

    try:
        while True:
            # 接收消息
            message = await websocket.receive_text()

            # 解析消息
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
            except json.JSONDecodeError:
                data = {"type": "raw", "data": message}
                msg_type = "raw"

            # 处理不同类型的消息
            if msg_type == "ping":
                # 收到 ping，回复 pong
                pong_response = {
                    "type": "pong",
                    "time": data.get("time", 0),
                    "server_time": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(pong_response))

            elif msg_type == "echo":
                # 回显消息
                echo_response = {
                    "type": "echo",
                    "message": data.get("message", ""),
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(echo_response))
                print(f"[>] 回显消息给 {client}: {data.get('message', '')}")

            elif msg_type == "chat":
                # AI 对话消息（旧版，保留兼容）
                user_message = data.get("message", "")
                print(f"[🤖] 收到来自 {client} 的提问(旧版chat): {user_message}")
                await websocket.send_text(
                    json.dumps(
                        {"type": "chat_error", "error": "请使用 agent_chat 消息类型"}
                    )
                )

            elif msg_type == "agent_chat":
                # Agent 对话消息
                user_message = data.get("message", "")
                session_id = data.get("session_id", "default")
                print(
                    f"[🤖] 收到来自 {client} 的Agent提问 (session: {session_id}): {user_message}"
                )

                try:
                    await agent.chat(user_message, session_id)
                    print(f"[✓] Agent 回复完成: {client} (session: {session_id})")
                except Exception as e:
                    error_msg = f"Agent 调用失败: {str(e)}"
                    print(f"[!] {error_msg}")
                    await websocket.send_text(
                        json.dumps({"type": "error", "error": error_msg})
                    )

            else:
                # 未知类型，原样返回
                await websocket.send_text(json.dumps({"type": "unknown", "received": data}))

    except WebSocketDisconnect:
        print(f"[-] 客户端断开: {client}")
    except Exception as e:
        print(f"[!] 与 {client} 通信时出错: {e}")


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
