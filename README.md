<div align="center">
  <h1>🛒 AutoCheckout Hub</h1>
  <p><strong>A centralized, high-performance checkout automation system with a Next.js Dashboard and Discord integration.</strong></p>
</div>

---

## 🌟 Overview
**AutoCheckout Hub** is a multi-site retail automation platform designed to monitor and check out items as soon as they drop. The system supports headless and visible browser orchestration using Selenium (`undetected-chromedriver`) and Playwright. 

It is controlled through a centralized **Next.js Dashboard** and offers real-time remote-control capabilities through **Discord**.

## 🚀 Features
- **Centralized Dashboard:** Add, remove, and manage monitoring tasks for specific SKUs directly from a beautiful Next.js web interface.
- **Process Isolation:** Every checkout task runs as an independent subprocess with its own isolated Chrome profile. If one bot crashes, the others remain entirely unaffected.
- **Discord Remote Control:** Receive live system logs (errors, captchas, checkouts) straight to a Discord channel.
- **Captcha Handling:** If a bot hits a captcha or login screen, it automatically **pauses**, notifies you via Discord, and waits for your remote `enter <task_id>` command to resume after you solve it.
- **Stop Control:** Easily kill hung browsers instantly with the Discord `stop <task_id>` command or via the Dashboard.

## 🛠 Tech Stack
- **Backend:** Python, FastAPI, SQLite (SQLAlchemy)
- **Frontend:** Next.js (React), TailwindCSS, Framer Motion
- **Automation:** `undetected-chromedriver` (Target, BestBuy, Topps), `playwright` (Walmart)
- **Integrations:** `discord.py`

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pythonicshariful/AutoCheckoutHub.git
   cd AutoCheckoutHub
   ```

2. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install fastapi uvicorn sqlalchemy python-dotenv discord.py requests undetected-chromedriver playwright loguru bs4
   playwright install chromium
   ```

3. **Install Frontend Dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Environment Variables:**
   Create a `.env` file in the `backend/` folder:
   ```env
   DISCORD_WEBHOOK_URL=your_webhook_url
   DISCORD_BOT_TOKEN=your_bot_token
   DISCORD_CHANNEL_ID=your_channel_id
   ```

## 💻 Usage

Start the **Backend API** (from the `backend` folder):
```bash
python -m uvicorn main:app --reload --port 8000
```

Start the **Frontend Dashboard** (from the `frontend` folder):
```bash
npm run dev
```

Open `http://localhost:3000` in your browser. From here, you can add SKUs, select the target site (Target, Walmart, BestBuy, Topps), and click **Run**!

## 📱 Discord Commands
Once the bot is added to your server, you can manage active tasks by typing commands directly into your text channel:
- `enter <task_id>`: Resumes a paused bot (useful after solving a captcha remotely).
- `stop <task_id>`: Forcibly terminates the bot process and closes its browser.

---
*Disclaimer: This tool is intended for educational purposes and personal use.*
