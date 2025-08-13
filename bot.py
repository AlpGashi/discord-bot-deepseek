import os
import discord
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup

# Load tokens from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Discord setup with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Model to use from DeepSeek
MODEL = "deepseek-chat"

# Conversation memory per channel
conversation_history = {}

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ----- /ask command -----
    if message.content.startswith("/ask"):
        channel_id = message.channel.id
        prompt = message.content[len("/ask "):].strip()
        if not prompt:
            await message.channel.send("Please provide a question. Example: `/ask What is AI?`")
            return

        await message.channel.send("Thinking... 🤖")

        # Initialize history for this channel if it doesn't exist
        if channel_id not in conversation_history:
            conversation_history[channel_id] = []

        # Add user message to history
        conversation_history[channel_id].append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": conversation_history[channel_id]
                }
            )

            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                answer = data["choices"][0]["message"]["content"]
                # Add assistant response to history
                conversation_history[channel_id].append({"role": "assistant", "content": answer})
                await message.channel.send(answer[:2000])  # Discord message limit
            else:
                await message.channel.send("❌ No response from AI.")

        except Exception as e:
            await message.channel.send(f"⚠️ Error: {e}")

    # ----- /summarize command -----
    elif message.content.startswith("/summarize"):
        url = message.content[len("/summarize "):].strip()
        if not url:
            await message.channel.send("Please provide a URL. Example: `/summarize https://example.com`")
            return

        await message.channel.send("Fetching and summarizing... 🤖")

        try:
            # Fetch page and extract text
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n")
            text = text[:3000]  # limit to avoid huge API requests

            # Send to DeepSeek for summary
            ds_response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": f"Summarize this page:\n{text}"}]
                }
            )

            data = ds_response.json()
            if "choices" in data and len(data["choices"]) > 0:
                summary = data["choices"][0]["message"]["content"]
                await message.channel.send(summary[:2000])
            else:
                await message.channel.send("❌ Could not get summary.")

        except Exception as e:
            await message.channel.send(f"⚠️ Error: {e}")

# ----- Minimal HTTP server to keep Render happy -----
PORT = int(os.getenv("PORT", 8000))

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    server = HTTPServer(('', PORT), SimpleHandler)
    print(f"HTTP server running on port {PORT}")
    server.serve_forever()

# Start HTTP server in background thread
threading.Thread(target=run_server, daemon=True).start()

# Start Discord bot
client.run(DISCORD_TOKEN)
