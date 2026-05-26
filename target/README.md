
# Target.com Purchase Automation Bot

This project automates the purchase process on **Target.com** using Selenium and Tkinter GUI.
It allows the user to log in, load SKUs from a CSV file, and automatically add items to the cart
and proceed through checkout.

---

## Features
- GUI-based bot with live console output.
- Auto-login persistence using Chrome profiles.
- Reads SKUs and quantities from a CSV file.
- Optional spending and buying limits via `config.json`.
- Auto-fills password and CVV during checkout.
- Supports stopping and resuming the bot.
- Threaded GUI interaction (no freezing during operation).

---

## Files
- **main.py** – Core bot script.
- **config.json** – Configuration file for CVE, SPEND_LIMIT, and BUY_LIMIT.
- **sku.csv** – CSV file with SKU and quantity columns.
- **cookies.pkl** – Stores session cookies.
- **local_storage.json** – Stores local storage data (if needed).
- **chrome_profile/** – Folder containing saved Chrome session.
- **README.md** – This file.

---

## Requirements
- Python 3.8+
- Google Chrome installed
- ChromeDriver (matching Chrome version)
- Required Python modules:

```bash
pip install selenium requests
```

---

## Usage

1. Clone the repository:

```bash
git clone https://github.com/pythonicshariful/purchase-atomation-target.com.git
```

2. Run the bot:

```bash
python main.py
```

3. When prompted, log in to Target manually and press **Enter** in the GUI.

4. The bot will automatically process SKUs from `sku.csv`.

---

## Configuration

Edit `config.json` to modify settings:

```json
{
  "CVE": "123",
  "SPEND_LIMIT": 120.00,
  "BUY_LIMIT": 3
}
```

---

## License

This project is for educational purposes only. Use responsibly.

**GitHub Repository:** [pythonicshariful/purchase-atomation-target.com](https://github.com/pythonicshariful/purchase-atomation-target.com/)
