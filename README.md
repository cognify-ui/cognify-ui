# 🧠 Cognify AI — Free Multi-Model AI Chatbot

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Try_Now-brightgreen?style=for-the-badge&logo=githubpages)](https://cognify-ui.github.io)
[![GitHub Pages](https://img.shields.io/badge/Hosted_on-GitHub_Pages-blue?style=flat-square&logo=github)](https://pages.github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-f7df1e?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

[![GitHub stars](https://img.shields.io/github/stars/cognify-ui/cognify-ui.github.io?style=social)](https://github.com/cognify-ui/cognify-ui.github.io/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cognify-ui/cognify-ui.github.io?style=social)](https://github.com/cognify-ui/cognify-ui.github.io/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/cognify-ui/cognify-ui.github.io?style=social)](https://github.com/cognify-ui/cognify-ui.github.io/watchers)

> **Chat with 4 powerful AI models in one interface — completely free, no login required, no API keys needed.**

👉 **[TRY IT NOW: cognify-ui.github.io](https://cognify-ui.github.io)** 👈

---

## ✨ Features That Make Cognify AI Unique

| Feature | What You Get |
|---------|---------------|
| 🤖 **4 AI Models in One Place** | Groq (lightning fast), Cerebras, Cloudflare AI, Google Gemini |
| 🌐 **Bilingual Interface** | Russian / English — switch instantly with settings saved |
| 📰 **Live AI News Feed** | Updated every hour with latest artificial intelligence news |
| 💾 **Local Storage Privacy** | Your chats never leave your browser — no servers, no tracking |
| 🔗 **Share Conversations** | Export chats to Telegram, WhatsApp, VK, Twitter with one click |
| 🎨 **Modern Glassmorphism UI** | Beautiful design with smooth animations |
| 📱 **Fully Responsive** | Works perfectly on desktop, tablet, and mobile |
| 🔑 **No Account Needed** | Start chatting immediately — zero friction |

## 🎯 Why Cognify AI Beats the Alternatives

| Capability | Cognify AI | ChatGPT (Free) | Gemini (Free) | Claude (Free) |
|------------|------------|----------------|---------------|---------------|
| **Multiple AI models** | ✅ 4 models | ❌ 1 model | ❌ 1 model | ❌ 1 model |
| **No login required** | ✅ Yes | ❌ Required | ❌ Required | ❌ Required |
| **Built-in AI news** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Chat sharing** | ✅ Yes (5 platforms) | ❌ No (paid feature) | ❌ No | ❌ No |
| **Local storage** | ✅ Yes (private) | ❌ Server storage | ❌ Server storage | ❌ Server storage |
| **Completely free** | ✅ Yes | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited |

## 📸 Screenshots

### Main Chat Interface
![Cognify AI Chat Interface](./screenshot-main.png)

### AI News Panel
![AI News Feed](./screenshot-news.png)

## 🚀 Quick Start Guide

### Option 1: Use Online (Recommended)
Just open **[cognify-ui.github.io](https://cognify-ui.github.io)** and start typing. That's it!

### Option 2: Run Locally (For Developers)
```bash
# Clone the repository
git clone https://github.com/cognify-ui/cognify-ui.github.io.git
cd cognify-ui.github.io

# No build step! Just open index.html in your browser
open index.html        # macOS
start index.html       # Windows
xdg-open index.html    # Linux

# Or use a local server (optional)
python -m http.server 8000
# Then visit http://localhost:8000
Option 3: Update News Feed Locally (For Contributors)
bash
# Install dependencies
pip install -r requirements.txt

# Run the news generator
python news_generator.py

# This will fetch latest AI news from RSS feeds and update news.json
🛠️ Technology Stack
Frontend
Pure Vanilla JavaScript (no frameworks — faster and lighter)

HTML5 + CSS3 with modern flexbox/grid layouts

Responsive design with mobile-first approach

Backend (Minimal)
GitHub Pages for hosting (100% free, CDN included)

GitHub Actions for hourly news updates

Browser LocalStorage for chat persistence

APIs Used
API	Speed	Best For	Free Tier
Groq	⚡⚡⚡ (Fastest)	Quick answers, coding	Yes
Cerebras	⚡⚡ (Very Fast)	General knowledge	Yes
Cloudflare AI	⚡ (Fast)	Lightweight tasks	Yes
Google Gemini	🐢 (Slower but smarter)	Complex reasoning	Yes (limited)
📁 Project Structure Explained
text
cognify-ui.github.io/
├── 📄 index.html              # Main chat application (2000+ lines)
├── 📄 login.html              # Authentication modal
├── 📄 register.html           # Registration modal
├── 📄 news.json               # AI news data (updated hourly)
├── 🐍 news_generator.py       # Python script to fetch RSS feeds
├── 📄 requirements.txt        # Python dependencies
├── 📄 sitemap.xml             # SEO sitemap for search engines
├── 📄 robots.txt              # Search engine crawling rules
├── 📄 humans.txt              # Credits to developers
├── 🖼️ og-image.png            # Open Graph image for social sharing
└── 📁 .github/
    └── 📁 workflows/
        └── 📄 news-updater.yml # GitHub Actions cron job
🔄 How Automatic News Updates Work
yaml
# This runs every hour via GitHub Actions
schedule:
  - cron: '0 * * * *'  # At minute 0 of every hour

# What happens:
# 1. GitHub spins up a Ubuntu container
# 2. Installs Python + dependencies
# 3. Runs news_generator.py
# 4. Fetches latest AI news from RSS feeds
# 5. Updates news.json
# 6. Commits and pushes changes automatically
🤝 How to Contribute
We welcome contributions! See CONTRIBUTING.md for detailed guide.

Quick Contribution Ideas
Skill Level	Task	Difficulty
Beginner	Fix typos in README	⭐
Beginner	Add more RSS sources to news_generator.py	⭐⭐
Intermediate	Add dark mode toggle	⭐⭐⭐
Intermediate	Implement model comparison feature	⭐⭐⭐⭐
Advanced	Add support for local LLM (Ollama)	⭐⭐⭐⭐⭐
📊 GitHub Statistics
https://img.shields.io/github/last-commit/cognify-ui/cognify-ui.github.io
https://img.shields.io/github/issues/cognify-ui/cognify-ui.github.io
https://img.shields.io/github/issues-pr/cognify-ui/cognify-ui.github.io
https://img.shields.io/github/repo-size/cognify-ui/cognify-ui.github.io

🌟 Star History
https://api.star-history.com/svg?repos=cognify-ui/cognify-ui.github.io&type=Date

📝 License
This project is licensed under the MIT License — see LICENSE file for details.

You can:

✅ Use commercially

✅ Modify and distribute

✅ Use privately

✅ Fork and create your own version

You cannot:

❌ Hold us liable (standard disclaimer)

🙏 Acknowledgments
Groq for incredibly fast inference

Google for Gemini API

Cloudflare for Workers AI

Cerebras for their amazing speed

All open-source RSS feeds for AI news

📞 Contact & Support
Report bugs: Open an issue

Feature requests: Open a discussion

⭐ If you find this useful, please star the repository! ⭐
Made with 🧠 by Cognify AI Team — cognify-ui.github.io
