import discord
from discord.ext import commands
from discord import app_commands
import random 
import graphic as gr

# Default ordered list of 35 Pokemon for the grid
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


# Main interactive game view handling turns, dynamic lists, and 5 row select menus
class LockoutGameView(discord.ui.View):
    def __init__(self, fp: discord.Member, sp: discord.Member, custom_list: list = None):
        super().__init__(timeout=None)
        self.players = [fp, sp]
        self.current_turn = 0
        self.teams = {fp: [], sp: []}
        # Use provided custom list or fall back to ALL_POKEMON default list
        self.pokemon_list = custom_list if custom_list else ALL_POKEMON
        self.update_selects()

    def update_selects(self):
        self.clear_items()
        picked = self.teams[self.players[0]] + self.teams[self.players[1]]
        row_letters = ["A", "B", "C", "D", "E"]

        # Generate one select menu per row (5 rows of 7 Pokemon each)
        for i in range(5):
            row_pokemon = self.pokemon_list[i * 7 : (i + 1) * 7]
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
        # Generate grid image buffer using graphic module with active pokemon list
        buffer = await gr.generate_lockout_grid(
            self.pokemon_list, 
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
        # Disable all row select dropdowns
        for item in self.children:
            item.disabled = True

        p1 = self.players[0]
        p2 = self.players[1]

        # Generate team summary image
        buffer = await gr.generate_teams_summary(
            self.teams[p1], 
            self.teams[p2],
            p1.display_name,
            p2.display_name
        )
        file = discord.File(fp=buffer, filename="teams_summary.png")

        # Format team listings in text
        red_team_str = "\n".join([f"• {p}" for p in self.teams[p1]])
        green_team_str = "\n".join([f"• {p}" for p in self.teams[p2]])

        embed_g = discord.Embed(
            title="35 Lockout — Final Teams",
            description="Draft complete! Here are the selected teams for both players:",
            color=discord.Color.gold()
        )
        embed_g.add_field(name=f"🟥 {p1.display_name}'s Team", value=red_team_str, inline=True)
        embed_g.add_field(name=f"🟩 {p2.display_name}'s Team", value=green_team_str, inline=True)
        embed_g.set_image(url="attachment://teams_summary.png")

        await interaction.edit_original_response(embed=embed_g, view=self, attachments=[file])


# Function to initialize the match embed (handles slash command deferral safely)
async def game(fp, sp, interaction: discord.Interaction, pokemon_list: list = None):
    game_view = LockoutGameView(fp, sp, pokemon_list)
    embed_g, file = await game_view.create_game_embed_and_file()

    # Send message using followup if response was deferred, otherwise standard send
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed_g, view=game_view, file=file)
    else:
        await interaction.channel.send(embed=embed_g, view=game_view, file=file)


# Waiting room view for players to join
class MyView(discord.ui.View):
    def __init__(self, pokemon_list: list = None):
        super().__init__(timeout=None) 
        self.Players_In = []  # should contain max 2 players
        self.pokemon_list = pokemon_list  # Store validated custom list

    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="mon_bouton_action")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        # # Check to avoid same player joining twice
        # if user in self.Players_In:
        #     await interaction.response.send_message("You already joined!", ephemeral=True)
        #     return

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
            
            # Start game with custom verified list (or default list if None)
            await game(first_p, sec_p, interaction, self.pokemon_list)


def create_embed_and_view(pokemon_list: list = None):
    embed = discord.Embed(
        title="35 Lockout waiting room", 
        description="Click on join to join",
        color=discord.Color.blue()
    )
    
    # Pass verified list to MyView instance
    view = MyView(pokemon_list=pokemon_list)
    return embed, view