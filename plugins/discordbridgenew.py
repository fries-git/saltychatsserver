import asyncio
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from logger import Logger
from db import channels
from handlers.websocket_utils import broadcast_to_all

import discord
from discord.ext import commands

server_data = None
_bot_started = False

sharedchannels = []
originwebhooks = []

env_path = Path(__file__).parent / 'discordBridge.env'
load_dotenv(dotenv_path=env_path)

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID')
DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

discord_gateway = DISCORD_BOT_TOKEN
directory_path = os.path.join('.', 'db', 'channels')


def channelsinit():
    global originchannels
    originchannels = []
    for entry in os.listdir(directory_path):
        full_path = os.path.join(directory_path, entry)
        if os.path.isfile(full_path):
            originchannels.append(Path(entry).stem)


channelsinit()
print(originchannels)


def trigger_event(ws, data, payload, s_data):
    global server_data
    server_data = s_data
    Logger.info("discordBridge received server_data")


def init(plugin_manager):
    plugin_manager.register_event("server_start", trigger_event)


async def start_bot():
    global _bot_started
    if _bot_started:
        return
    _bot_started = True
    await bot.start(DISCORD_BOT_TOKEN)


def start():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())


@bot.event
async def on_ready():
    global discordchannels
    discordchannels = []
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        print(f"\nGuild: {guild.name} (ID: {guild.id})")
        for channel in guild.channels:
            if channel.type == discord.ChannelType.text:
                discordchannels.append(channel.name)
    Logger.info(f"Total channels found: {len(discordchannels)}")

    global sharedchannels
    sharedchannels = list(set(originchannels) & set(discordchannels))
    print(f"Discord Channels: {discordchannels}")
    print(f"Origin Channels: {originchannels}")
    print(f"Shared Channels: {sharedchannels}")


@bot.event
async def on_message(message):
    if message.author.bot:
        Logger.info(f"Message received from bot '{message.channel.name}', ignoring: {message.content}")
        return

    if not message.guild or message.guild.id != int(DISCORD_GUILD_ID):
        Logger.info(f"Message received in non-correct guild '{message.channel.name}', ignoring: {message.content}")
        return

    if message.channel.name in sharedchannels:
        Logger.info(f"Message received in shared channel '{message.channel.name}': {message.content}")

        send_message = {
            "user": "originChats",
            "content": message.content,
            "timestamp": time.time(),
            "id": str(uuid.uuid4())
        }

        channels.save_channel_message(message.channel.name, send_message)

        if server_data and server_data.get("connected_clients"):
            await broadcast_to_all(
                server_data["connected_clients"],
                {
                    "cmd": "message_new",
                    "message": send_message,
                    "channel": message.channel.name,
                    "global": True
                }
            )
        else:
            Logger.warning("discordBridge: server_data or connected_clients not ready yet")
    else:
        Logger.info(f"Message received in non-shared channel '{message.channel.name}', ignoring: {message.content}")
        return


start()