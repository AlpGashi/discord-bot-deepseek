import os
import discord
import requests


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Discord setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Model to use from OpenRouter
MODEL = "openai/gpt-3.5-turbo"  # you can change to another supported model

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!ask"):
        prompt = message.content[len("!ask "):].strip()
        if not prompt:
            await message.channel.send("Please provide a question. Example: `!ask What is AI?`")
            return

        await message.channel.send("Thinking... 🤖")

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                answer = data["choices"][0]["message"]["content"]
                await message.channel.send(answer[:2000])  # Discord limit
            else:
                await message.channel.send("❌ No response from AI.")

        except Exception as e:
            await message.channel.send(f"⚠️ Error: {e}")



conversation_history = {}

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!ask"):
        channel_id = message.channel.id
        prompt = message.content[len("!ask "):].strip()
        if not prompt:
            await message.channel.send("Please provide a question. Example: `!ask What is AI?`")
            return

        await message.channel.send("Thinking... 🤖")

        # Initialize history for channel if not exist
        if channel_id not in conversation_history:
            conversation_history[channel_id] = []

        # Add user's new prompt to conversation history
        conversation_history[channel_id].append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
                # Add AI's answer to conversation history
                conversation_history[channel_id].append({"role": "assistant", "content": answer})
                await message.channel.send(answer[:2000])
            else:
                await message.channel.send("❌ No response from AI.")

        except Exception as e:
            await message.channel.send(f"⚠️ Error: {e}")

            
client.run(DISCORD_TOKEN)