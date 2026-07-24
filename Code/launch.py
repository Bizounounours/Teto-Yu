import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import _35MonsUU as _35UU


# --- CONFIGURATION ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- SYNCHRONISATION ---
@bot.event
async def on_ready():
    print(f"[{bot.user.name}'s Breads of Ruin]")
    try:
        # This sends your @bot.tree.commands to Discord's servers
        synced = await bot.tree.sync() 
        print(f"{len(synced)} PP of Overheat")
    except Exception as e:
        print(f"Error syncing: {e}")

# --- COMMANDES ---

@bot.tree.command(name="hello", description="Say hello")
async def hello_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello I'm {bot.user.name}")

@bot.tree.command(name="test", description="Send test embed")
async def hello_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=_35UU.test())

# --- LAUNCH ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)