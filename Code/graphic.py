import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont

COLOR_WHITE = (245, 245, 245)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
ROW_LETTERS = ["A", "B", "C", "D", "E"]

async def generate_lockout_grid(pokemon_list, team_red, team_green):
    cols, rows = 7, 5
    cell_size = 120
    border_width = 3
    margin_left = 40  # Extra space on the left for row letters (A, B, C, D, E)

    img_width = (cols * cell_size) + margin_left
    img_height = rows * cell_size

    grid_img = Image.new("RGB", (img_width, img_height), "black")
    draw = ImageDraw.Draw(grid_img)

    try:
        font = ImageFont.truetype("arial.ttf", 10)
        letter_font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
        letter_font = ImageFont.load_default()

    # Draw row letters on the left side
    for row_idx, letter in enumerate(ROW_LETTERS):
        ly = (row_idx * cell_size) + (cell_size // 2) - 10
        draw.text((12, ly), letter, fill="white", font=letter_font)

    async with aiohttp.ClientSession() as session:
        for idx, pkmn in enumerate(pokemon_list):
            row = idx // cols
            col = idx % cols

            # Offset x position by margin_left
            x1 = margin_left + (col * cell_size)
            y1 = row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            if pkmn in team_red:
                bg_color = COLOR_RED
            elif pkmn in team_green:
                bg_color = COLOR_GREEN
            else:
                bg_color = COLOR_WHITE

            draw.rectangle([x1, y1, x2, y2], fill=bg_color, outline="black", width=border_width)

            clean_name = pkmn.lower().replace(" ", "").replace("-", "").replace(".", "")
            sprite_url = f"https://play.pokemonshowdown.com/sprites/gen5/{clean_name}.png"

            try:
                async with session.get(sprite_url) as resp:
                    if resp.status == 200:
                        sprite_data = await resp.read()
                        sprite = Image.open(io.BytesIO(sprite_data)).convert("RGBA")
                        sprite.thumbnail((cell_size - 25, cell_size - 30))
                        
                        px = x1 + (cell_size - sprite.width) // 2
                        py = y1 + (cell_size - 15 - sprite.height) // 2
                        grid_img.paste(sprite, (px, py), sprite)
            except Exception:
                pass

            text_bbox = draw.textbbox((0, 0), pkmn, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = x1 + (cell_size - text_width) // 2
            text_y = y2 - 14

            draw.text((text_x, text_y), pkmn, fill="black", font=font)

    buffer = io.BytesIO()
    grid_img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer