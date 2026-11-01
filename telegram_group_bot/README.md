# 🌸 Riya — AI Telegram Group Manager Bot

A Telegram Group Manager bot with a sweet, playful girl persona named **Riya**, powered by **Google Gemini AI** for natural conversational chatting, an **Admin Broadcast System**, and moderation tools.

---

## ✨ Features Overview

### 💬 1. Girl Persona & AI Chat Companion
* **Warm & Playful Persona:** Riya acts like a sweet, charming 19-year-old girl who loves chatting, using expressive emojis (🌸, ✨, 💖, 🥰, 🎀), and keeping group vibes positive.
* **Powered by Gemini AI:** Uses Google Gemini (or seamless fallback) to hold natural conversations.
* **Smart Memory:** Remembers recent conversation context per user and chat.
* **How to Chat with Riya:**
  * **In Groups:** Mention her name (*"Hey Riya, how was your day?"*), tag `@her_bot_username`, or reply directly to any of her messages.
  * **In Private (DM):** Send any message directly to have a 1-on-1 chat!

---

### 📢 2. Admin Broadcast Feature (`/bcast` / `/broadcast`)
* **Restricted to Bot Owners:** Normal members or regular group admins cannot trigger broadcasts. Only IDs in `OWNER_IDS` can broadcast.
* **Broadcast to Every Group:** Automatically reaches every group where Riya has been added.
* **Rich Media & Forward Support:** Reply to photos, videos, stickers, voice notes, or forwarded announcements with `/bcast` to send the exact media to all groups.
* **Auto-Pin Option:** Use `/bcast -pin [message]` to broadcast and automatically pin the announcement in all groups.
* **Live Progress & Summary Report:** Real-time counter showing successful deliveries, inactive/kicked groups, and duration.

---

### 🛡️ 3. Complete Group Moderation
* `/ban [reply/id] [reason]` — Bans a member from the group.
* `/unban [id]` — Unbans a user.
* `/kick [reply/id]` — Removes member with ability to rejoin.
* `/mute [reply/id] [duration]` — Restricts user from sending messages (e.g. `10m`, `2h`, `1d`).
* `/unmute [reply/id]` — Restores speaking permissions.
* `/warn [reply/id]` — Issues a warning strike. At 3 strikes (customizable), automatically bans user!
* `/warns` & `/resetwarns` — View or reset warning strikes.
* `/del` — Instantly deletes replied message.
* `/purge [count]` — Bulk deletes up to 100 recent messages.
* `/pin` & `/unpin` — Pin or unpin messages.
* `/lock [links|stickers|media]` — Restrict specific content for non-admins.
* `/unlock [type]` & `/locks` — Remove locks or view active restrictions.
* `/rules` & `/setrules [text]` — View or update group rules.

---

### ⚙️ 4. Interactive Settings Dashboard (`/settings`)
Group admins can toggle features on/off instantly via interactive inline buttons:
* 🌸 **Welcome Greetings** (ON / OFF)
* 💬 **AI Companion Chat** (ON / OFF)
* 🔗 **Anti-Link Filter** (ON / OFF)

---

### 💌 5. Aesthetic Welcomes & Goodbyes
* Clean HTML welcome card displaying member's name, user ID, member count, and group rules button.
* Sweet departure messages when members leave.

---

### 🎮 6. Fun & Community Engagement
* `/afk [reason]` — Go AFK with reason and timer; notifies anyone who mentions you and automatically clears when you send a message.
* `/flirt` — Sweet compliments and playful pick-up lines.
* `/roast [reply]` — Lighthearted, witty roasts.
* `/ship [reply/name]` — Couples compatibility meter (0–100%) with love bar and cute commentary.
* `/truth` & `/dare` — Party game questions and challenges.
* `/flip` & `/roll` — Coin toss and dice roll.
* `/info [reply]` — Stylish User Profile ID card.
* `/chatinfo` — Group overview card.

---

### 📌 7. Group Notes System
* `/save [name] [text/media]` — Save custom notes or media.
* `#name` or `/get [name]` — Retrieve saved notes.
* `/notes` — List all saved notes in the group.
* `/clear [name]` — Delete a saved note.

---

## 🚀 Quick Setup Guide

### Step 1: Create Your Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a display name (e.g., `Riya ✨`), and a username ending in `bot` (e.g., `RiyaGroupManagerBot`).
3. Copy the **HTTP API Token**.

### Step 2: Get Your Telegram User ID
1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram and press **Start**.
2. Copy your numeric **Id** (e.g., `123456789`).

### Step 3: (Optional) Get Free Gemini AI Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and generate a free API key.
*(Note: If left empty, Riya will still chat using her built-in cute conversational engine!)*

### Step 4: Configure `.env`
Open `.env` in the `telegram_group_bot` folder and fill in:
```env
BOT_TOKEN=your_bot_token_from_botfather
OWNER_IDS=your_numeric_user_id
GEMINI_API_KEY=your_gemini_api_key_optional
```

### Step 5: Start Riya!
* **On Windows:** Double-click `run.bat`
* **Or via Terminal:**
  ```bash
  python bot.py
  ```

---

## 👑 Adding Riya to Your Groups
1. Open your group, tap **Add Members**, and search for your bot's username.
2. Promote Riya to **Admin** with permissions:
   * Delete messages
   * Ban users
   * Pin messages
   * Invite users via link
3. Type `/start` or `/help` to begin! 🌸
