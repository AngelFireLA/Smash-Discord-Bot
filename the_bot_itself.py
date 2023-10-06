import asyncio
import csv
import re
from heapq import nlargest
from random import randint

import aiohttp
import aiosqlite
import bing_image_urls
import discord
import numpy as np
from bs4 import BeautifulSoup
from discord.ext import commands
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

min_id = 1
max_id = 30363


async def fetch(url, session, retries=3, delay=0.1):
    for i in range(retries):
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Error {response.status} on {url}. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

    return None


async def parse_character_image(html):
    soup = BeautifulSoup(html, 'html.parser')

    detail_element = soup.find('img', id="profilethumb")
    src_value = detail_element.get('src')

    return src_value


async def parse_anime_name(html):
    soup = BeautifulSoup(html, 'html.parser')

    # find the 'td' element with text "From"
    from_element = soup.find('th', string='From')

    # find the 'a' element within the next 'td' element
    anime_element = from_element.find_next_sibling('td').find('a')

    # ensure anime_element is not None before accessing its text attribute
    anime_name = anime_element.text if anime_element else None

    return anime_name


async def get_characters_by_attribute(attribute_value, attribute_column):
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Execute an SQL query to fetch characters with the specified attribute value
            query = f'SELECT * FROM characters WHERE {attribute_column} = ?'
            await c.execute(query, (attribute_value,))

            # Fetch all characters with the specified attribute value
            matching_characters = await c.fetchall()

    characters = []
    for character_info in matching_characters:
        c_id, name, height, weight, bust, waist, hip, gender, eye_color, hair_color, hair_length, apparent_age, animal_ears = character_info
        characters.append(
            {'id': c_id, 'name': name, 'height': height, 'weight': weight, 'bust': bust, 'waist': waist, 'hip': hip,
             'gender': gender, 'eye_color': eye_color, 'hair_color': hair_color, 'hair_length': hair_length,
             'apparent_age': apparent_age, 'animal_ears': animal_ears})

    return characters, matching_characters


async def add_character_to_liked(user_id, character_id, character_name, message):
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Check if the entry already exists
            existing_entry = await c.execute('SELECT 1 FROM liked_characters WHERE user_id = ? AND character_id = ?',
                                             (user_id, character_id))
            if await existing_entry.fetchone():
                await message.channel.send(f"Vous avez déja smash {character_name}!")
                return  # Exit the function if entry exists

            # Get the current date and time
            import datetime
            liked_on = datetime.datetime.now()

            # Execute an SQL query to add the liked character for the user
            await c.execute('INSERT INTO liked_characters(user_id, character_id, liked_on) VALUES(?, ?, ?)',
                            (user_id, character_id, liked_on))
            await conn.commit()
            await message.channel.send(f"{character_name} a été smash par {message.author.display_name}")


async def remove_character_from_liked(user_id, character_id):
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Execute an SQL query to remove the liked character for the user
            await c.execute('DELETE FROM liked_characters WHERE user_id = ? AND character_id = ?',
                            (user_id, character_id))
            await conn.commit()


async def get_liked_characters(user_id):
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Execute an SQL query to fetch all characters liked by the user
            await c.execute(
                'SELECT characters.* FROM characters JOIN liked_characters ON characters.id = liked_characters.character_id WHERE liked_characters.user_id = ?',
                (user_id,))
            liked_characters = await c.fetchall()
    characters = []
    for character_info in liked_characters:
        c_id, name, height, weight, bust, waist, hip, gender, eye_color, hair_color, hair_length, apparent_age, animal_ears = character_info
        characters.append(
            {'id': c_id, 'name': name, 'height': height, 'weight': weight, 'bust': bust, 'waist': waist, 'hip': hip,
             'gender': gender, 'eye_color': eye_color, 'hair_color': hair_color, 'hair_length': hair_length,
             'apparent_age': apparent_age, 'animal_ears': animal_ears})

    return characters, liked_characters


async def create_user_if_not_exists(user_id, username):
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Check if the user ID already exists in the users table
            await c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            existing_user = await c.fetchone()

            # If the user ID doesn't exist, insert the user into the users table
            if not existing_user:
                await c.execute('INSERT INTO users(id, username) VALUES(?, ?)', (user_id, username))
                await conn.commit()


async def get_character_image(mode, c_id, character_name=None):
    print("Character ID is :", str(c_id))
    modes = ["bing", "character_database"]
    if mode not in modes:
        mode = "bing"
    if not character_name:
        character_name = (await get_characters_by_attribute(c_id, "id"))[0][0]['name']
    print("Character Name is :", character_name)
    if mode == "bing":

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            url = None
            with open("anime_characters_links_full.csv", newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["Name"] == character_name:
                        url = row["Link"]
            try:
                page_html = await fetch(url, session)
                if page_html is not None:
                    anime_name = await parse_anime_name(page_html)
                    print("Anime Name :", anime_name)
            except aiohttp.client_exceptions.ClientConnectorError:
                await asyncio.sleep(2)
                try:
                    page_html = await fetch(url, session)
                    if page_html is not None:
                        anime_name = await parse_anime_name(page_html)
                        print("Anime Name :", anime_name)
                except aiohttp.client_exceptions.ClientConnectorError:
                    await asyncio.sleep(2)
                    try:
                        page_html = await fetch(url, session)
                        if page_html is not None:
                            anime_name = await parse_anime_name(page_html)
                            print("Anime Name :", anime_name)
                    except aiohttp.client_exceptions.ClientConnectorError:
                        await asyncio.sleep(2)

        with open('image_search.txt', 'r') as file:
            content = file.read()
        loop = asyncio.get_running_loop()
        character_links = await loop.run_in_executor(None, bing_image_urls.bing_image_urls,
                                                     f'{character_name} {content} {anime_name}', True)
        i = 0
        character_link = character_links[i]
        while character_link.startswith("https://ami.animecharactersdatabase.com") or not (
                character_link.endswith(".jpg") or character_link.endswith(".png") or character_link.endswith(
                ".gif") or character_link.endswith(".jpeg") or character_link.endswith(
                ".svg") or character_link.endswith(".webp")):
            try:
                character_link = character_links[i]
                i += 1
            except IndexError:
                while not (
                        character_link.endswith(".jpg") or character_link.endswith(".png") or character_link.endswith(
                        ".gif") or character_link.endswith(".jpeg") or character_link.endswith(
                        ".svg") or character_link.endswith(".webp")):
                    i -= 1
                    print(character_link[i])
                    try:
                        character_link = character_links[i]
                        print(character_link[i])
                    except IndexError:
                        await asyncio.sleep(2)
                        print(i)
                        print()
                    if i > 0:
                        print(i)

        print("mode :", character_link)
        return character_link
    elif mode == "character_database":
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            url = None
            with open("anime_characters_links_full.csv", newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["Name"] == character_name:
                        url = row["Link"]

            page_html = await fetch(url, session)
            if page_html is not None:
                character_image_link = await parse_character_image(page_html)
                print("mode :", character_image_link)
                return character_image_link


characteristics_dict = {
    "Gender": {
        "Female ": 1
    },

    "Eye Color": {
        "Blue ": 1,
        "Pink ": 2,
        "Brown ": 3,
        "Blue / Green ": 4,
        "Green ": 5,
        "Red ": 6,
        "Yellow ": 7,
        "Purple ": 8,
        "Orange ": 9,
        "Gray ": 10,
        "Not Visible ": 11,
        "Black ": 12,
        "White ": 13,
        "Unknown ": 14
    },

    "Hair Color": {
        "Red ": 1,
        "Blonde ": 2,
        "Brown ": 3,
        "Black ": 4,
        "Blue ": 5,
        "Gray ": 6,
        "Orange ": 7,
        "Green ": 8,
        "Pink ": 9,
        "Purple ": 10,
        "Maroon ": 11,
        "White ": 12,
        "Blue / Green ": 13,
        "Unknown ": 14,
        "Not Visible ": 15
    },

    "Hair Length": {
        "Past Waist ": 1,
        "To Waist ": 2,
        "To Neck ": 3,
        "To Shoulders ": 4,
        "To Chest ": 5,
        "To Ears ": 6,
        "Hair Up / Indeterminate ": 7,
        "No Hair ": 8,
        "Unknown ": 9
    },

    "Apparent Age": {
        "Teen ": 1,
        "Adult ": 2,
        "Child ": 3
    },

    "Animal Ears": {
        "No ": 1,
        "Elf ": 2,
        "Animal ": 3,
        "Horns ": 4,
        "Yes ": 5,
        "Unknown ": 6,
        None: 7
    }
}


def extract_number(string):
    if string is None:
        return None
    cleaned_string = re.sub(r'[^0-9\s]', '', string)
    number = re.search(r'\d+', cleaned_string)
    if number:
        return int(number.group())
    else:
        return None


def convert_character_to_numbered_dict(character_info):
    try:
        c_id, name, height, weight, bust, waist, hip, gender, eye_color, hair_color, hair_length, apparent_age, animal_ears = character_info
    except ValueError:
        print(character_info)
        raise ValueError("Character info is not correct")
    character = {'id': c_id, 'name': name, 'Height': extract_number(height), 'Weight': extract_number(weight),
                 'Bust': extract_number(bust), 'Waist': extract_number(waist), 'Hip': extract_number(hip),
                 'Gender': gender, 'Eye Color': eye_color, 'Hair Color': hair_color, 'Hair Length': hair_length,
                 'Apparent Age': apparent_age, 'Animal Ears': animal_ears}
    character_with_attributes_as_numbers = {k: characteristics_dict[k][v] if k in characteristics_dict else v for k, v
                                            in character.items()}
    return character_with_attributes_as_numbers


async def get_all_characters():
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Execute an SQL query to fetch all characters
            await c.execute('SELECT * FROM characters')
            all_characters = await c.fetchall()

    # Return all characters
    return all_characters


TOKEN = 'MTE0MTMzMTIwNzQ0Mzk5MjY5Nw.GO6o-i.mTfzfvsrcunUpqK-cQ_aLqO78Jx8Bgj2qbUX6Q'

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


class MyView(discord.ui.View):
    def __init__(self, img_links):
        super().__init__()
        self.img_links = img_links
        self.current_img_index = 0

    async def update_embed_image(self, embed):
        img_link = self.img_links[self.current_img_index]
        embed.set_image(url=img_link)

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.grey)
    async def button_previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_img_index = (self.current_img_index - 1) % len(self.img_links)
        await self.update_embed_image(interaction.message.embeds[0])
        await interaction.response.edit_message(embed=interaction.message.embeds[0])

    @discord.ui.button(label='Next', style=discord.ButtonStyle.grey)
    async def button_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_img_index = (self.current_img_index + 1) % len(self.img_links)
        await self.update_embed_image(interaction.message.embeds[0])
        await interaction.response.edit_message(embed=interaction.message.embeds[0])


@bot.event
async def on_ready():
    print(f'Connected')
    await bot.change_presence(activity=discord.Game(name="Regarde des animés"))


@bot.slash_command(name="get_character_by_id")
async def get_character_by_id_command(message, character_id: int):
    global last_character_id
    await message.response.defer()
    await create_user_if_not_exists(message.author.id, message.author.display_name)
    last_character_id = character_id
    character_name = (await get_characters_by_attribute(character_id, "id"))[0][0]['name']
    img_link1 = await get_character_image("bing", character_id, character_name)
    img_link2 = await get_character_image("character_database", character_id, character_name)
    if img_link2 and not img_link1:
        img_link1 = img_link2
        await message.followup.send("Un problème est survenu et il n'y aura pas d'image bing.")
    if not img_link2 and img_link1:
        await message.followup.send("Un problème est survenu et il n'y aura pas d'image classique.")
        img_link2 = img_link1
    elif not img_link2 and not img_link1:
        await message.followup.send("Un problème est survenu, aucune image n'a été trouvée")
    embed = discord.Embed(title=character_name, description=f"id : {character_id}", color=0x109319)
    embed.add_field(name=character_name, value=character_name)
    embed.set_image(url=img_link2)
    view = MyView([img_link2, img_link1])
    await message.followup.send(embed=embed, view=view)


@bot.slash_command(name="get_character_recommandation",
                   description="Prédit un perso que vous aimerez basé sur votre liste de perso like")
async def get_recommandation_command(message, user_id=None):
    await message.response.defer()
    await create_user_if_not_exists(message.author.id, message.author.display_name)
    if not user_id:
        user_id = message.author.id  # Replace with the actual user ID

    # Retrieve the liked characters for the user
    liked_characters = await get_liked_characters(user_id)
    liked_characters = liked_characters[1]

    # Retrieve all characters
    all_characters = await get_all_characters()

    # Convert characters to feature vectors
    liked_feature_vectors = [list(convert_character_to_numbered_dict(char).values())[2:] for char in liked_characters]
    all_feature_vectors = [list(convert_character_to_numbered_dict(char).values())[2:] for char in all_characters]

    # Convert lists of feature vectors to numpy arrays
    liked_feature_array = np.array(liked_feature_vectors)
    all_feature_array = np.array(all_feature_vectors)

    # Create an imputer object that uses the mean imputation method
    from sklearn.impute import SimpleImputer
    imputer = SimpleImputer(strategy='mean')

    # Apply the imputer to the feature arrays
    liked_feature_array = imputer.fit_transform(liked_feature_array)
    all_feature_array = imputer.transform(all_feature_array)

    # # Create and fit a KNN model
    # k = 1  # Number of neighbors to consider
    # knn_model = NearestNeighbors(n_neighbors=k, algorithm='ball_tree').fit(all_feature_array)
    #
    # # Find k nearest neighbors for each liked character
    # nearest_neighbors = []
    # for liked_character in liked_feature_array:
    #     distances, indices = knn_model.kneighbors([liked_character])
    #     nearest_neighbors.extend(indices[0])
    #
    # # Find the character that appears most frequently in the nearest neighbors
    # from collections import Counter
    # counter = Counter(nearest_neighbors)
    # most_common_character_index = counter.most_common(1)[0][0]
    #
    # for char_index, count in counter.most_common():
    #     character = all_characters[char_index]
    #     if character not in liked_characters:
    #         # Print the most common character that is not in the liked characters
    #         await message.channel.send(
    #             f"The character that the user might like next is: {character[1]}  of id {all_characters[most_common_character_index][0]}")  # Index 1 for 'name'
    #         break  # Exit the loop after finding the recommendation

    k = 5
    # Calculate cosine similarities
    similarities = cosine_similarity(all_feature_array, liked_feature_array)

    # Find the top-k characters with the highest cosine similarities that are not in the liked characters
    suggestions = []
    for i, character in enumerate(all_characters):
        if character not in liked_characters:
            similarity = np.max(similarities[i])  # Get the highest similarity with any liked character
            suggestions.append((character, similarity))

    top_k_suggestions = nlargest(k, suggestions, key=lambda x: x[1])  # Get the top-k suggestions based on similarity
    ans = "Suggestions:\n"
    # Print the suggestions
    if top_k_suggestions:
        for suggestion in top_k_suggestions:
            ans+=(f"- {suggestion[0][0]}\n")  # Index 1 for 'name'
        await message.respond(ans)
    else:
        await message.respond("No suggestions found.")


@bot.slash_command(name="get_character_info")
async def get_character_info_command(message, character_id: int):
    await create_user_if_not_exists(message.author.id, message.author.display_name)

    answer = ""
    character = await get_characters_by_attribute(character_id, "id")
    for i, v in character[0][0].items():
        print(i)
        answer += str(i).capitalize().replace("_", " ") + ": " + str(v) + "\n"
    await message.respond(answer)


last_character_id = None


@bot.slash_command(name="smash_or_pass",
                   description="Envoyer 'smash' pour smasher le personnage, envoyer 'pass' pour passer")
async def get_random_character_command(message):
    global last_character_id
    await message.response.defer()
    await create_user_if_not_exists(message.author.id, message.author.display_name)
    character_id = randint(min_id, max_id)
    last_character_id = character_id
    character_name = (await get_characters_by_attribute(character_id, "id"))[0][0]['name']
    img_link1 = await get_character_image("bing", character_id, character_name)
    img_link2 = await get_character_image("character_database", character_id, character_name)
    if img_link2 and not img_link1:
        img_link1 = img_link2
        await message.followup.send("Un problème est survenu et il n'y aura pas d'image bing.")
    if not img_link2 and img_link1:
        await message.followup.send("Un problème est survenu et il n'y aura pas d'image classique.")
        img_link2 = img_link1
    elif not img_link2 and not img_link1:
        await message.followup.send("Un problème est survenu, aucune image n'a été trouvée")
    embed = discord.Embed(title=character_name, description=f"Rang : {character_id}", color=0x109319)
    embed.add_field(name=character_name, value=character_name)
    embed.set_image(url=img_link2)
    view = MyView([img_link2, img_link1])
    await message.followup.send(embed=embed, view=view)


@bot.slash_command(name="get_character_by_attribute")
async def get_character_by_attribute_command(message: discord.Message,
                                             attribute: discord.Option(str, choices=['id', 'name',
                                                                                     'height',
                                                                                     'weight',
                                                                                     'bust',
                                                                                     'waist',
                                                                                     'hip',
                                                                                     'gender',
                                                                                     'eye_color',
                                                                                     'hair_color',
                                                                                     'hair_length',
                                                                                     'apparent_age',
                                                                                     'animal_ears']), value: str):
    await create_user_if_not_exists(message.author.id, message.author.display_name)

    character = await get_characters_by_attribute(value, attribute)
    answer = ""
    print(character[0])
    for i, v in character[0][0].items():
        answer += str(i).capitalize().replace("_", " ") + ": " + str(v) + "\n"
    await message.respond(answer)


# Admin only command to add a liked character of a specific id assigned to a specific user id to the database
@bot.slash_command(name="add_character_to_liked")
@commands.has_role("Gérant")
async def add_character_to_liked_command(message, user_id, character_id: int):
    user_id = int(user_id)
    # get discord username of the discord user_id:
    user = await bot.fetch_user(user_id)
    await create_user_if_not_exists(user_id, user.display_name)
    character_name = (await get_characters_by_attribute(character_id, "id"))[0][0]['name']

    await add_character_to_liked(user_id, character_id, character_name, message)


# Now to remove a liked character of a specific id assigned to a specific user id from the database

@bot.slash_command(name="remove_character_from_liked")
@commands.has_role("Gérant")
async def remove_character_from_liked_command(message, user_id, character_id: int):
    user_id = int(user_id)
    # get discord username of the discord user_id:
    user = await bot.fetch_user(user_id)
    await create_user_if_not_exists(user_id, user.display_name)
    await remove_character_from_liked(user_id, character_id)
    await message.respond("Character removed from liked characters")


# Admin command to get the list of characters liked by a specific user id
@bot.slash_command(name="get_liked_characters")
@commands.has_role("Gérant")
async def get_liked_characters_command(message, user_id=None):
    if not user_id:
        user_id = message.author.id
    user_id = int(user_id)
    # get discord username of the discord user_id:
    user = await bot.fetch_user(user_id)
    await create_user_if_not_exists(user_id, user.display_name)
    characters = await get_liked_characters(user_id)

    answer = ""
    for c in characters[0]:
        answer += f"Id : {c['id']} Name: {c['name']} \n"
    await message.respond(answer)


@bot.event
async def on_message(message: discord.Message):
    global last_character_id
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    if message.content.lower().startswith("smash"):
        if not last_character_id:
            async for msg in message.channel.history(limit=100):
                # Check if message is from the bot
                if msg.author == bot.user:
                    if msg.embeds:
                        embed = msg.embeds[0]
                        character_name = embed.title
                        character_id = (await get_characters_by_attribute(character_name, "name"))[0][0]['id']
                        last_character_id = character_id
                        await add_character_to_liked(message.author.id, character_id, character_name, message)

                        break
        else:
            character_id = last_character_id
            character_name = (await get_characters_by_attribute(character_id, "id"))[0][0]['name']

            await add_character_to_liked(message.author.id, character_id, character_name, message)


bot.run(TOKEN)
