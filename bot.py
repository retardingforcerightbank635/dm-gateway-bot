"""私聊中转机器人：验证通过后才转发消息（支持文字/表情包/图片/文件/视频/语音等）"""
import os
import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# 配置（通过环境变量传入，不要硬编码）
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储待验证用户和已验证用户
pending_users = {}  # user_id: {"answer": str}
verified_users = set()

# Captcha 题目
CAPTCHAS = [
    ("Tap 🐶", "🐶"),
    ("Tap 🐱", "🐱"),
    ("Tap 🐼", "🐼"),
    ("Tap 🦊", "🦊"),
    ("Tap 🐸", "🐸"),
    ("Tap 🦁", "🦁"),
]

def generate_captcha():
    q, a = random.choice(CAPTCHAS)
    emojis = ["🐶", "🐱", "🐼", "🦊", "🐸", "🦁"]
    options = emojis.copy()
    random.shuffle(options)
    buttons = [InlineKeyboardButton(e, callback_data=f"verify:{e}") for e in options]
    keyboard = InlineKeyboardMarkup([buttons])
    return q, a, keyboard


async def start(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
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

    if selected == pending_users[user_id]["answer"]:
        verified_users.add(user_id)
        del pending_users[user_id]
        await query.edit_message_text("✅ 验证通过！你的消息将转达给主人。主人回复后你会收到通知。")
    else:
        await query.answer("❌ 选择错误，请重试", show_alert=True)


async def forward_to_owner(context, user_id: int, user_name: str, message):
    """将用户消息转发给主人，支持各种消息类型。"""
    header = f"💬 来自 {user_name} 的消息：\n用户 ID: {user_id}\n"
    caption_suffix = f"\n\n用户 ID: {user_id}"
    msg = message

    if msg.text:
        await context.bot.send_message(OWNER_ID, f"{header}\n{msg.text}")

    elif msg.sticker:
        # 先发头部信息，再转发贴纸
        await context.bot.send_message(OWNER_ID, header)
        await context.bot.send_sticker(OWNER_ID, msg.sticker.file_id)

    elif msg.photo:
        photo = msg.photo[-1]  # 最高分辨率
        cap = (msg.caption or "") + caption_suffix
        await context.bot.send_photo(OWNER_ID, photo.file_id, caption=f"{header}{cap}")

    elif msg.video:
        cap = (msg.caption or "") + caption_suffix
        await context.bot.send_video(OWNER_ID, msg.video.file_id, caption=f"{header}{cap}")

    elif msg.video_note:
        await context.bot.send_message(OWNER_ID, header)
        await context.bot.send_video_note(OWNER_ID, msg.video_note.file_id)

    elif msg.voice:
        cap = (msg.caption or "") + caption_suffix
        await context.bot.send_voice(OWNER_ID, msg.voice.file_id, caption=f"{header}{cap}")

    elif msg.audio:
        cap = (msg.caption or "") + caption_suffix
        await context.bot.send_audio(OWNER_ID, msg.audio.file_id, caption=f"{header}{cap}")

    elif msg.document:
        cap = (msg.caption or "") + caption_suffix
        await context.bot.send_document(OWNER_ID, msg.document.file_id, caption=f"{header}{cap}")

    elif msg.animation:  # GIF
        cap = (msg.caption or "") + caption_suffix
        await context.bot.send_animation(OWNER_ID, msg.animation.file_id, caption=f"{header}{cap}")

    elif msg.location:
        await context.bot.send_message(OWNER_ID, header)
        await context.bot.send_location(OWNER_ID, msg.location.latitude, msg.location.longitude)

    elif msg.contact:
        await context.bot.send_message(OWNER_ID, header)
        await context.bot.send_contact(
            OWNER_ID,
            phone_number=msg.contact.phone_number,
            first_name=msg.contact.first_name,
            last_name=msg.contact.last_name or "",
        )

    else:
        # 兜底：直接 forward
        await context.bot.send_message(OWNER_ID, header)
        await msg.forward(OWNER_ID)


async def reply_to_user(context, target_id: int, message):
    """将主人的回复原样转发给用户，支持各种消息类型。"""
    prefix = "💬 主人回复：\n"
    msg = message

    if msg.text:
        await context.bot.send_message(target_id, f"{prefix}{msg.text}")
    elif msg.sticker:
        await context.bot.send_sticker(target_id, msg.sticker.file_id)
    elif msg.photo:
        photo = msg.photo[-1]
        await context.bot.send_photo(target_id, photo.file_id, caption=msg.caption or "")
    elif msg.video:
        await context.bot.send_video(target_id, msg.video.file_id, caption=msg.caption or "")
    elif msg.video_note:
        await context.bot.send_video_note(target_id, msg.video_note.file_id)
    elif msg.voice:
        await context.bot.send_voice(target_id, msg.voice.file_id, caption=msg.caption or "")
    elif msg.audio:
        await context.bot.send_audio(target_id, msg.audio.file_id, caption=msg.caption or "")
    elif msg.document:
        await context.bot.send_document(target_id, msg.document.file_id, caption=msg.caption or "")
    elif msg.animation:
        await context.bot.send_animation(target_id, msg.animation.file_id, caption=msg.caption or "")
    elif msg.location:
        await context.bot.send_location(target_id, msg.location.latitude, msg.location.longitude)
    else:
        await msg.forward(target_id)


def extract_user_id_from_header(text: str):
    """从转发头部提取用户 ID。"""
    if text and "用户 ID:" in text:
        try:
            return int(text.split("用户 ID:")[1].split("\n")[0].strip())
        except Exception:
            pass
    return None


async def handle_message(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "未知"
    msg = update.message

    # 忽略命令
    if msg.text and msg.text.startswith("/"):
        return

    # ── 管理员逻辑 ──
    if user_id == OWNER_ID:
        if msg.reply_to_message:
            # 尝试从被回复消息的文字中提取用户 ID
            replied = msg.reply_to_message
            source_text = replied.text or replied.caption or ""
            target_id = extract_user_id_from_header(source_text)
            if target_id:
                await reply_to_user(context, target_id, msg)
                return
        await msg.reply_text("请回复某条转发消息来回复对应用户。")
        return

    # ── 未验证用户 ──
    if user_id not in verified_users:
        q, answer, keyboard = generate_captcha()
        pending_users[user_id] = {"answer": answer}
        await msg.reply_text(
            f"🤖 请先验证你是真人：\n\n{q}",
            reply_markup=keyboard
        )
        return

    # ── 已验证用户，转发给主人 ──
    await forward_to_owner(context, user_id, user_name, msg)
    await msg.reply_text("✅ 已发送给主人，等待回复...")


async def post_init(application: Application):
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
