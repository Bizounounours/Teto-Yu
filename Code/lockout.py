import discord
from discord.ext import commands
from discord import app_commands
import random 
import graphic as gr

# Ordered list of all 35 Pokemon for the grid
ALL_POKEMON = [
    "Shiinotic", "Scolipede", "Clodsire", "Aggron", "Tropius", "Vigoroth", "Aerodactyl",
    "Puppitar", "Lokix", "Flapple", "Garganacl", "Unfezant", "Tyranitar", "Leafeon",
    "Bidoof", "Slaking", "Miltank", "Trevenant", "Cursola", "Tinkaton", "Watchog",
    "Talonflame", "Gengar", "Perrserker", "Dunsparce", "Wigglytuff", "Pikachu", "Scizor",
    "Grapploct", "Banette", "Greavard", "Delphox", "Shuckle", "Muk", "Amoonguss"
]

# Dropdown select menu for choosing a Pokemon from a specific row
class PokemonSelect(discord.ui.Select):
    def __init__(self, pokemon_list, placeholder, custom_id):
        options = [discord.SelectOption(label=p, value=p) for p in pokemon_list]
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        game_view: LockoutGameView = self.view
        selected = self.values[0]

        # Check if it is the current player's turn
        current_player = game_view.players[game_view.current_turn]
        if interaction.user != current_player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        # Acknowledge interaction to prevent Discord timeout during image generation
        await interaction.response.defer()

        # Save selected Pokemon to the player's team
        game_view.teams[current_player].append(selected)
        game_view.current_turn = (game_view.current_turn + 1) % 2

        # Check game end condition (6 picks per player = 12 total)
        total_picks = sum(len(team) for team in game_view.teams.values())
        if total_picks >= 12:
            await game_view.finish_game(interaction)
            return

        # Update row selects and regenerate the grid image
        game_view.update_selects()
        embed_g, file = await game_view.create_game_embed_and_file()
        await interaction.edit_original_response(embed=embed_g, view=game_view, attachments=[file])


# Main interactive game view handling turns and 5 row select menus
class LockoutGameView(discord.ui.View):
    def __init__(self, fp: discord.Member, sp: discord.Member):
        super().__init__(timeout=None)
        self.players = [fp, sp]
        self.current_turn = 0
        self.teams = {fp: [], sp: []}
        self.update_selects()

    def update_selects(self):
        self.clear_items()
        picked = self.teams[self.players[0]] + self.teams[self.players[1]]
        row_letters = ["A", "B", "C", "D", "E"]

        # Generate one select menu per row (5 rows of 7 Pokemon)
        for i in range(5):
            row_pokemon = ALL_POKEMON[i * 7 : (i + 1) * 7]
            available_in_row = [p for p in row_pokemon if p not in picked]

            # Add select menu only if there are remaining Pokemon in this row
            if available_in_row:
                letter = row_letters[i]
                self.add_item(PokemonSelect(
                    available_in_row, 
                    f"Row {letter} ({len(available_in_row)} left)", 
                    f"select_row_{letter}"
                ))

    async def create_game_embed_and_file(self):
        # Generate grid image buffer using graphic module
        buffer = await gr.generate_lockout_grid(
            ALL_POKEMON, 
            self.teams[self.players[0]], 
            self.teams[self.players[1]]
        )
        file = discord.File(fp=buffer, filename="grid.png")

        next_player = self.players[self.current_turn]
        embed_g = discord.Embed(
            title="35 Lockout — Game Grid",
            description=(
                f"Turn: {next_player.mention}\n\n"
                f"🟥 **{self.players[0].display_name}** ({len(self.teams[self.players[0]])}/6)\n"
                f"🟩 **{self.players[1].display_name}** ({len(self.teams[self.players[1]])}/6)"
            ),
            color=discord.Color.blue()
        )
        embed_g.set_image(url="attachment://grid.png")
        return embed_g, file

    async def finish_game(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True

        buffer = await gr.generate_lockout_grid(
            ALL_POKEMON, 
            self.teams[self.players[0]], 
            self.teams[self.players[1]]
        )
        file = discord.File(fp=buffer, filename="grid.png")

        embed_g = discord.Embed(
            title="35 Lockout — Draft Finished!",
            description="Both teams are complete!",
            color=discord.Color.gold()
        )
        embed_g.set_image(url="attachment://grid.png")
        await interaction.edit_original_response(embed=embed_g, view=self, attachments=[file])


# Function to initialize the match embed
async def game(fp, sp, interaction):
    game_view = LockoutGameView(fp, sp)
    embed_g, file = await game_view.create_game_embed_and_file()
    await interaction.channel.send(embed=embed_g, view=game_view, file=file)


# Waiting room view for players to join
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 
        self.Players_In = []  # should contain max 2 players

    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="mon_bouton_action")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        # Check to avoid same player joining twice
        if user in self.Players_In:
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return

        # Add players to verification list
        self.Players_In.append(user)

        # Embed that needs modification
        embed = interaction.message.embeds[0]

        # Adding a field for the player
        embed.add_field(
            name=f"Player {len(self.Players_In)}", 
            value=user.mention, 
            inline=False
        )

        # Disable button when lobby is full
        if len(self.Players_In) == 2:
            button.disabled = True

        # Embed Edit
        await interaction.response.edit_message(embed=embed, view=self)

        # Enough players ? (2)
        if len(self.Players_In) == 2:
            first_p = random.choice(self.Players_In)
            sec_p = self.Players_In[0]
            if sec_p == first_p:
                sec_p = self.Players_In[1]
            
            # Start the game with image grid
            await game(first_p, sec_p, interaction)


def create_embed_and_view():
    embed = discord.Embed(
        title="35 Lockout waiting room", 
        description="Click on join to join",
        color=discord.Color.blue()
    )
    
    view = MyView()
    return embed, view