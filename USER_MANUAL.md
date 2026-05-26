# AutoCheckout Hub - Full User Manual (A to Z)

Welcome to your customized AutoCheckout Hub! This system is designed to monitor and automate checkouts for Target, BestBuy, Walmart, and Topps. It features an interactive dashboard, real-time logging, Discord integration for remote control, and a scalable architecture that prevents bot crashes by isolating each task.

---

## 1. System Requirements & Setup

Before running the hub, ensure you have the correct environment set up.

### Prerequisites
1. **Python 3.10+** (Required for the backend and bots).
2. **Node.js 18+** (Required for the Next.js Dashboard).
3. **Google Chrome** installed on your Windows machine.

### Installation Steps
1. **Install Python Dependencies:**
   Open a terminal in the `backend` folder and run:
   ```bash
   pip install fastapi uvicorn sqlalchemy python-dotenv discord.py requests undetected-chromedriver playwright loguru bs4
   ```
   *Note: For Walmart to work, you must also install the Playwright browsers by running:*
   ```bash
   playwright install chromium
   ```

2. **Install Frontend Dependencies:**
   Open a terminal in the `frontend` folder and run:
   ```bash
   npm install
   ```

---

## 2. Configuring Discord Integration

The system uses Discord both to send you live logs and to accept remote commands (like un-pausing bots).

### Setting up the `.env` File
In your `backend` folder, there must be a file named `.env`. If it doesn't exist, create it. It should look like this:

```env
# The webhook URL where the bot will push log messages
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Your Discord Bot Token (used for reading commands like "enter 10")
DISCORD_BOT_TOKEN=MTUwNjU1...

# The specific Channel ID where the bot should listen for your commands
DISCORD_CHANNEL_ID=1506555386101235865
```

### Adding the Bot to Your Server (Crucial for receiving commands)
To read your commands (like `enter 12` or `stop 12`), your actual Discord Application must be invited to your server:
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and log in.
2. Click your bot application. On the left menu, go to **Bot**, scroll down to **Privileged Gateway Intents**, and toggle **ON** the `MESSAGE CONTENT INTENT`. Save changes.
3. On the left menu, click **OAuth2** -> **URL Generator**.
4. Under "Scopes", check **`bot`**. Under "Bot Permissions", check **`Read Messages/View Channels`** and **`Send Messages`**.
5. Copy the generated URL at the bottom, paste it in a new tab, and Authorize it to join your server.

### Changing the Discord Settings
If you ever want to change the channel or bot token:
1. Open `backend/.env`.
2. Replace `DISCORD_WEBHOOK_URL` with a new webhook link.
3. Replace `DISCORD_BOT_TOKEN` with a new bot token.
4. Replace `DISCORD_CHANNEL_ID` with the ID of the new text channel (Right-click a channel in Discord and select "Copy Channel ID").
5. **Restart the Backend** for changes to take effect.


---

## 3. Starting the System

To use the Hub, you need to start **both** the backend and the frontend.

1. **Start the Backend (API & Bots):**
   Open a terminal in `g:\Personal\fver\fiverr\backend` and run:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   *Leave this terminal open in the background.*

2. **Start the Frontend (Dashboard):**
   Open a new terminal in `g:\Personal\fver\fiverr\frontend` and run:
   ```bash
   npm run dev
   ```
   *Leave this terminal open as well.*

3. **Open the Dashboard:**
   Open your browser and navigate to **http://localhost:3000**.

---

## 4. Using the Dashboard (A to Z)

The dashboard is your centralized command center.

### Adding a SKU
1. In the **Monitored SKUs** section, type the product SKU (e.g., `94681777`).
2. Select the Site from the dropdown (Target, Walmart, BestBuy, Topps).
3. Select the desired Quantity.
4. Click **Add**. The SKU will be saved to your local database and appear in the table below.

### Running a Bot
1. Find the SKU you want to run in the table.
2. Click the green **Play (▶)** button under Actions.
3. The bot will instantly launch in the background. A physical Google Chrome window will appear on your screen, operating entirely on its own.
4. *Note: You can click Play on multiple SKUs at the same time. The system creates isolated Chrome profiles for every task so they never crash each other.*

### Monitoring Progress
1. Watch the **System Logs** section on the bottom right.
2. You will see live updates like `[INFO] Bot browser starting...`, `[INFO] Added to cart!`, or `[SUCCESS] Task Finished`.

---

## 5. Handling Captchas & Logins (Remote Control)

Sometimes, bots get blocked by Captchas, or a site like Walmart requires you to log in to proceed. **The bot will not crash.** Instead, it will **Pause**.

### What happens when a bot pauses?
- The Dashboard will show the task status in orange as **Paused**.
- The System Logs (and your Discord channel) will warn you: `[ERROR] Not logged in` or `[ERROR] Captcha detected`.
- The physical Chrome browser will freeze, allowing you time to solve the issue.

### How to Resume (Option 1: Dashboard)
1. Go to the open Chrome window and manually solve the Captcha or log into your account.
2. Go back to your Dashboard.
3. In the **Active Tasks** panel, click the orange **Resume** button next to the paused task.
4. The bot will instantly wake up and continue!

### How to Resume (Option 2: Discord)
If you are away from your PC and using a remote desktop viewer on your phone:
1. You will see a notification in Discord that Task `10` is paused.
2. Go to your remote viewer, solve the Captcha on the PC.
3. In your Discord channel, simply type:
   ```text
   enter 10
   ```
4. The Discord Bot will reply `✅ Sent enter keystroke to Task 10`, and the bot on your PC will instantly resume checkout!

### How to Stop a Task
If you want to permanently kill a bot (whether it's running or paused):
- **From Dashboard:** Click the **Red Square (Stop)** button next to the spinning loader icon in the SKU table.
- **From Discord:** Type `stop 10` (replace 10 with your Task ID). The bot will securely terminate the process and close the browser.

---

## 6. Where is the Data Stored?

- **Database:** All tasks, SKUs, and logs are stored locally in `backend/checkout.db` (a SQLite database).
- **Chrome Profiles:** Every time a bot runs, it creates an isolated folder in `C:\temp\profile_<task_id>`. This stores cookies. If you log into Walmart on Task 5, Task 5 will remember your login forever.

---

## 7. Troubleshooting

- **"Failed to reach backend"**: Ensure the python `uvicorn` terminal is still running without errors.
- **Bot opens then closes immediately**: The bot likely threw an error before it could even start. Check the `backend` terminal for raw python tracebacks.
- **Playwright errors**: If Walmart fails to start, ensure you ran `playwright install chromium` in your backend folder.
