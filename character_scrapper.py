import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pc

async def fetch(url, session, retries=3, delay=0.1):
    for i in range(retries):
        try:
            async with session.get(url) as response:
                print(response.status)
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error {response.status} on {url}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        except Exception as e:
            print(f"Exception {e} on {url}. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    return None

async def parse_character_page(html, character_name):
    soup = BeautifulSoup(html, 'html.parser')

    # Extract measurements
    measurements = {}
    for measurement in ['Height', 'Weight', 'Bust', 'Waist', 'Hip']:
        measurement_element = soup.find('a', string=measurement)
        measurements[measurement] = measurement_element.find_next('td').text if measurement_element else None

    # Extract character details
    details = {}
    for detail in ['Gender', 'Eye Color', 'Hair Color', 'Hair Length', 'Apparent Age', 'Animal Ears']:
        detail_element = soup.find('th', string=detail)
        details[detail] = detail_element.find_next_sibling('td').text if detail_element else None

    # Combine all data into a single dictionary
    data = {
        'Character Name': character_name,
        **measurements,
        **details,
    }

    return data

async def main():
    df = pd.read_csv('anime_characters_links.csv')

    # Extract 'Name' and 'Link' columns and create a list of tuples
    character_ids = list(zip(df['Name'], df['Link']))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        data = []
        i = 0
        for character_name, character_id in character_ids:
            i+=1
            url = str(character_id)
            page_html = await fetch(url, session)
            if page_html is not None:
                character_data = await parse_character_page(page_html, character_name)
                df = pd.DataFrame([character_data])

                # Convert 'Bust' and 'Waist' columns to string type
                df['Bust'] = df['Bust'].astype(str)
                df['Waist'] = df['Waist'].astype(str)
                df['Hip'] = df['Hip'].astype(str)
                df['Weight'] = df['Weight'].astype(str)
                df['Height'] = df['Height'].astype(str)
                # Fill missing values with 0s
                df.fillna(0, inplace=True)

                with open('anime_characters_no_edit.csv', 'a', newline='', encoding='utf-8') as f:
                    df.to_csv(f, header=f.tell() == 0, index=False)
            print(f"Hello {i}!")

asyncio.run(main())
