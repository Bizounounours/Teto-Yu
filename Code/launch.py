import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import _35MonsUU as _35UU
import lockout as lcko


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

@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
# --- COMMANDS ---

@bot.tree.command(name="hello", description="Say hello")
async def hello_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello I'm {bot.user.name}")


# Command to launch a 35 Lockout waiting room with optional custom Pokemon list
@bot.tree.command(name="lockout", description="Launch a 35 Lockout waiting room")
@app_commands.describe(pokemon_list="Optional list of 35 Pokemon separated by newlines or commas")
async def lockout(interaction: discord.Interaction, pokemon_list: str = None):
    parsed_list = None

    # Verification and parsing of the custom Pokemon list
    if pokemon_list:
        # Replace commas and newlines with spaces to unify separators
        clean_text = pokemon_list.replace(",", " ").replace("\n", " ")
        # Split by spaces and remove empty entries
        parsed_list = [pkmn.strip() for pkmn in clean_text.split(" ") if pkmn.strip()]

        # Validation check: must have at least 35 Pokemon
        if len(parsed_list) != 35:
            await interaction.response.send_message(
                f"⚠️ The list must contain 35 Pokemons (you provided {len(parsed_list)}).", 
                ephemeral=True
            )
            return

    # Create waiting room embed and view with validated list
    embed, view = lcko.create_embed_and_view(parsed_list)
    await interaction.response.send_message(embed=embed, view=view)

# ---Test commands---

'''
@bot.tree.command(name="test", description="Send test embed")
async def test_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=_35UU.test())

@bot.tree.command(name="test_lockout", description="Lancer une partie de test solo")
async def test_lockout(interaction: discord.Interaction):
    # Lance directement le jeu avec toi et le bot
    await lcko.game(interaction.user, interaction.client.user, interaction)
'''


# --- LAUNCH ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)