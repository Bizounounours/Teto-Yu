import discord
from discord.ext import commands
from discord import app_commands

def test() :
    embedtest=discord.Embed(
        title="Test",
        color=discord.Color(0x90D5FF)
    )

    embedtest.add_field(
        name="Teto",
        value="Kasane"
    )
    return embedtest
