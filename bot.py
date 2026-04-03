"""私聊中转机器人：验证通过后才转发消息"""
import os
import logging
import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# 配置（通过环境变量传入，不要硬编码）
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储待验证用户和已验证用户
pending_users = {}  # user_id: {"challenge": answer, "message": pending_msg}
verified_users = set()  # 已通过验证的用户ID

# Captcha 题目
CAPTCHas = [
    ("Tap 🐶", "🐶"),
    ("Tap 🐱", "🐱"),
    ("Tap 🐼", "🐼"),
    ("Tap 🦊", "🦊"),
    ("Tap 🐸", "🐸"),
    ("Tap 🦁", "🦁"),
]

def generate_captcha():
    q, a = random.choice(CAPTCHas)
    emojis = ["🐶", "🐱", "🐼", "🦊", "🐸", "🦁"]
    options = emojis.copy()
    random.shuffle(options)
    buttons = [InlineKeyboardButton(e, callback_data=f"verify:{e}") for e in options]
    keyboard = InlineKeyboardMarkup([buttons])
    return q, a, keyboard

async def start(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user_id = update.effective_user.id

    if user_id == OWNER_ID:
        await update.message.reply_text("你是管理员，可以直接发消息给我，我会帮你转发。")
        return

    if user_id in verified_users:
        await update.message.reply_text("你已经通过验证，直接发消息给我即可转达给主人。")
    else:
        q, answer, keyboard = generate_captcha()
        pending_users[user_id] = {"answer": answer}
        await update.message.reply_text(
            f"🤖 你想联系主人，请先验证你是真人：\n\n{q}",
            reply_markup=keyboard
        )

async def handle_verify_callback(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    """处理验证回调"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if not data.startswith("verify:"):
        return

    selected = data.split(":")[1]

    if user_id not in pending_users:
        await query.edit_message_text("验证已超时，请重新发送 /start")
        return

    answer = pending_users[user_id]["answer"]

    if selected == answer:
        verified_users.add(user_id)
        del pending_users[user_id]
        await query.edit_message_text("✅ 验证通过！你的消息将转达给主人。主人回复后你会收到通知。")
    else:
        await query.answer("❌ 选择错误，请重试", show_alert=True)

async def handle_message(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    """处理私聊消息"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "未知"
    text = update.message.text or update.message.caption or ""

    # 忽略命令消息
    if text.startswith("/"):
        return

    # 管理员直接发消息
    if user_id == OWNER_ID:
        # 检查是否是回复消息
        if update.message.reply_to_message:
            # 从回复中提取目标用户ID
            forward_to = update.message.reply_to_message.text
            if "用户 ID:" in forward_to:
                try:
                    target_id = int(forward_to.split("用户 ID:")[1].split("\n")[0])
                    await context.bot.send_message(target_id, f"💬 主人回复：\n{text}")
                    return
                except:
                    pass
        await update.message.reply_text("这是你的机器人，你可以直接发送消息给用户。")
        return

    # 未验证用户
    if user_id not in verified_users:
        q, answer, keyboard = generate_captcha()
        pending_users[user_id] = {"answer": answer}
        await update.message.reply_text(
            f"🤖 请先验证你是真人：\n\n{q}",
            reply_markup=keyboard
        )
        return

    # 已验证用户，转发消息给主人
    forward_text = f"💬 来自 {user_name} 的消息：\n\n{text}\n\n用户 ID: {user_id}"
    await context.bot.send_message(OWNER_ID, forward_text)
    await update.message.reply_text("✅ 已发送给主人，等待回复...")

async def post_init(application: Application):
    """启动后通知主人"""
    await application.bot.send_message(OWNER_ID, "🤖 DM Gateway Bot 已启动！")

def main():
    if not BOT_TOKEN or not OWNER_ID:
        logger.error("请设置 BOT_TOKEN 和 OWNER_ID 环境变量")
        return

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_verify_callback))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
