import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pc

async def fetch(url, session, retries=5, delay=0.5):
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

async def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    character_elements = soup.find_all('li')
    print(len(character_elements))
    data = []
    for element in character_elements:
        link_element = element.find('a')

        name = link_element.text
        link = 'https://www.animecharactersdatabase.com/' + link_element['href']
        if not link.startswith('https://www.animecharactersdatabase.com/characters.php?id='):
            continue
        data.append((name, link))
    return data

async def main():
    num_pages = 1395
    characters_per_page = 50

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    async with aiohttp.ClientSession(headers=headers) as session:

        data = []
        i=0
        for page in range(num_pages):
            offset = i * characters_per_page
            i+=1
            url = f"https://www.animecharactersdatabase.com/sort_characters.php?x={str(offset)}&hair_color=&hair_length=&sex=2&mimikko=&age=3,4&eye_color=&r_eye_color=&r_hair_color=&r_hair_length=&r_sex=&r_mimikko=&r_age=&clothing=&lightdark=&otherchar=&role=&refs=&display=&max=&mode=&filter=&pid=&pids=&mt=&s7=&order=def"
            print(f"hello {i}")
            page_html = await fetch(url, session)
            if page_html is not None:
                data.extend(await parse(page_html))
            await asyncio.sleep(0.5)  # Add a 1-second delay between requests
        df = pd.DataFrame(data, columns=['Name', 'Link'])
        table = pa.Table.from_pandas(df)
        with pa.OSFile('anime_characters_links.csv', 'wb') as f:
            pc.write_csv(table, f)


asyncio.run(main())
