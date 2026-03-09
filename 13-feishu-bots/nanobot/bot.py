"""
飞书 Nanobot 桥接服务（长连接模式）
- 使用 WebSocket 长连接接收飞书事件，无需公网 IP
- 仅处理私聊消息，不获取群聊/其他聊天内容
- 通过 Ollama 调用本地免费模型
"""

import os
import json
import logging
import httpx
import lark_oapi as lark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FEISHU_APP_ID = os.environ["FEISHU_APP_ID"]
FEISHU_APP_SECRET = os.environ["FEISHU_APP_SECRET"]
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

# 用于去重的已处理消息 ID 集合
processed_msg_ids: set[str] = set()


def get_tenant_access_token() -> str:
    """获取飞书 tenant_access_token"""
    with httpx.Client() as client:
        resp = client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        )
        data = resp.json()
        if data.get("code") != 0:
            logger.error("获取 token 失败: %s", data)
            raise Exception(f"获取 token 失败: {data}")
        return data["tenant_access_token"]


def send_feishu_message(chat_id: str, text: str):
    """向飞书用户发送消息"""
    token = get_tenant_access_token()
    with httpx.Client() as client:
        resp = client.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )
        data = resp.json()
        if data.get("code") != 0:
            logger.error("发送消息失败: %s", data)


def chat_with_ollama(user_message: str) -> str:
    """调用 Ollama 本地模型生成回复"""
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个有帮助的AI助手，用中文回复。"},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                },
            )
            data = resp.json()
            return data["message"]["content"]
    except Exception as e:
        logger.error("Ollama 调用失败: %s", e)
        return f"抱歉，模型暂时不可用: {e}"


def handle_message(data: "lark.im.v1.P2ImMessageReceiveV1") -> None:
    """处理飞书消息事件"""
    try:
        event = data.event
        message_obj = event.message
        msg_id = message_obj.message_id or ""

        # 消息去重
        if msg_id in processed_msg_ids:
            return
        processed_msg_ids.add(msg_id)
        if len(processed_msg_ids) > 10000:
            processed_msg_ids.clear()

        # ===== 关键：仅处理私聊消息 =====
        chat_type = message_obj.chat_type or ""
        if chat_type != "p2p":
            logger.info("忽略非私聊消息: chat_type=%s", chat_type)
            return

        # 只处理文本消息
        msg_type = message_obj.message_type or ""
        chat_id = message_obj.chat_id or ""

        if msg_type != "text":
            if chat_id:
                send_feishu_message(chat_id, "目前只支持文本消息哦~")
            return

        # 解析消息内容
        content = json.loads(message_obj.content or "{}")
        user_text = content.get("text", "").strip()

        if not user_text:
            return

        logger.info("收到私聊消息: %s", user_text[:50])

        # 调用本地模型并回复
        reply = chat_with_ollama(user_text)
        send_feishu_message(chat_id, reply)

    except Exception as e:
        logger.error("处理消息异常: %s", e, exc_info=True)


def main():
    # 创建长连接事件处理器
    event_handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(handle_message)
        .build()
    )

    # 创建长连接客户端
    cli = lark.ws.Client(
        FEISHU_APP_ID,
        FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO,
    )

    logger.info("=== Nanobot 启动，通过长连接接收飞书消息 ===")
    cli.start()


if __name__ == "__main__":
    main()
