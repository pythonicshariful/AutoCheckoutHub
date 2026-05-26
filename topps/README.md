# Topps Purchase Automation Bot

A Python-based automation tool for purchasing products from Topps.com with a user-friendly GUI interface.

## 🚀 Features

- **GUI Interface**: Easy-to-use Tkinter-based graphical interface
- **Automated Purchase Flow**: Automatically adds products to cart and proceeds to checkout
- **Persistent Browser Profile**: Maintains login sessions and preferences
- **Undetected Chrome**: Uses undetected-chromedriver to avoid bot detection
- **Real-time Status Updates**: Live logging of bot activities
- **Manual Override**: Allows manual intervention for captchas and login

## 📋 Requirements

- Python 3.7+
- Chrome browser installed
- Internet connection

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pythonicshariful/purchase-atomation-topps.com
   cd purchase-atomation-topps.com
   ```

2. **Install required dependencies:**
   ```bash
   pip install undetected-chromedriver selenium tkinter
   ```

   Or create a requirements.txt file:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Configure the bot:**
   - Enter the product URL from Topps.com
   - Set the desired quantity
   - Click "Start Bot"

3. **Manual setup (if required):**
   - Complete any captcha challenges
   - Log in to your Topps account if not already logged in
   - The bot will wait for you to complete these steps

4. **Automated process:**
   - Bot navigates to the product page
   - Sets the specified quantity
   - Adds the product to cart
   - Proceeds to checkout
   - Attempts to complete the purchase

## ⚙️ Configuration

The bot uses a persistent Chrome profile stored in the `chrome_profile` directory, which:
- Maintains login sessions
- Saves browser preferences
- Reduces the need for repeated manual setup

## 🔧 Technical Details

### Dependencies
- `undetected-chromedriver`: Stealth Chrome automation
- `selenium`: Web browser automation
- `tkinter`: GUI framework (included with Python)

### Key Components
- **ToppsBotGUI**: Main GUI application class
- **create_driver()**: Chrome driver setup with persistent profile
- **run_bot()**: Core automation logic

### Browser Configuration
- Uses undetected Chrome driver to avoid detection
- Persistent user data directory
- Disabled automation indicators
- Remote debugging enabled

## ⚠️ Important Notes

- **Legal Compliance**: Ensure you comply with Topps.com's terms of service
- **Rate Limiting**: The bot includes random delays to avoid overwhelming the server
- **Manual Intervention**: You may need to complete captchas or login manually
- **Account Safety**: Use responsibly to avoid account suspension

## 🛡️ Safety Features

- Random delays between actions (3-5 seconds)
- Error handling for timeouts and missing elements
- Graceful shutdown capability
- Status logging for monitoring

## 🐛 Troubleshooting

### Common Issues

1. **Chrome not found**: Ensure Chrome browser is installed
2. **Element not found**: Website structure may have changed
3. **Timeout errors**: Check internet connection and website availability
4. **Login required**: Complete manual login in the browser window

### Error Messages
- `❌ Timeout`: Element not found within expected time
- `❌ Error`: General automation error
- `✅ Success`: Operation completed successfully

## 📝 License

This project is for educational purposes only. Please use responsibly and in accordance with the website's terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## ⚖️ Disclaimer

This tool is provided for educational and research purposes only. Users are responsible for ensuring their use complies with all applicable laws and website terms of service. The authors are not responsible for any misuse or consequences of using this software.
