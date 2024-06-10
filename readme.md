# 🐹 HamsterKombat Farmer Script

This is a Python-based script for the HamsterKombat game. It automates interactions with the "Hamster Kombat" API, performing actions such as "taps", purchasing boosts, claiming the daily bonus, and synchronizing the game state, all in a scheduled and asynchronous manner.

## 📋 Requirements

This project requires Python 3.11 and the following Python packages:

- aiohttp
- coloredlogs
- apscheduler
- python-dotenv
- Brotli

These can be installed using pip:

```bash
pip install -r requirements.txt
```

## 🐳 Docker

A Dockerfile is provided for running the bot in a Docker container. To build and run the Docker container:

```bash
docker build -t hamsterfarmer-bot .
docker run -d hamsterfarmer-bot
```

## 🚀 Usage

To run the bot, simply execute the main.py script:

```bash
python main.py
```

The bot will start and begin automating tasks in the game.

# ⚙️ Configuration
The bot uses environment variables for configuration. The `TOKEN` environment variable is required for the bot to authenticate with the HamsterKombat API.  You can set environment variables in a .env file. The bot uses the python-dotenv package to load these variables at runtime. 

## 👥 Contributors

- [ale](https://github.com/AlessTRV)
- [Razvyyh](https://github.com/Razvyyh)