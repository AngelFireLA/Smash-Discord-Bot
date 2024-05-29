import os
import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('images.db')
cursor = conn.cursor()

#ai_score is number between 0 and 1

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS images (
    id TEXT PRIMARY KEY,
    folder_path TEXT,
    direct_path TEXT,
    extension TEXT,
    label TEXT,
    labeled_by TEXT
    ai_score FLOAT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS image_metadata (
    id TEXT,
    key TEXT,
    value TEXT,
    FOREIGN KEY(id) REFERENCES images(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS image_tags (
    id TEXT PRIMARY KEY,
    tags TEXT,
    FOREIGN KEY(id) REFERENCES images(id)
)
''')


# Function to insert image metadata into the database
def insert_image_data(base_path):
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(('jpg', 'jpeg', 'png', 'gif')):
                file_path = os.path.join(root, file)
                folder_path = root
                file_id, extension = os.path.splitext(file)

                cursor.execute('''
                INSERT OR IGNORE INTO images (id, folder_path, direct_path, extension)
                VALUES (?, ?, ?, ?)
                ''', (file_id, folder_path, file_path, extension))


# Insert data for each dataset
datasets = [
    'dataset gatherer/fullbody/resized_ganime_fullbody_ultraclean',
    'dataset gatherer/nekos_api/images_nekosapi',
    'dataset gatherer/nekos_best/nekos_best_images',
    'dataset gatherer/nekos_moe/images',
    'dataset gatherer/waifu_im/waifu_images',
    'dataset gatherer/waifu_pics/images'
]

for dataset in datasets:
    insert_image_data(dataset)


# Function to insert metadata from image_metadata.csv
def insert_image_metadata(csv_path):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        image_id = os.path.splitext(os.path.basename(row['url']))[0]
        cursor.execute('''
        INSERT INTO image_metadata (id, key, value)
        VALUES (?, ?, ?)
        ''', (image_id, 'tags', row['tags']))
        if not pd.isna(row['characters']):
            cursor.execute('''
            INSERT INTO image_metadata (id, key, value)
            VALUES (?, ?, ?)
            ''', (image_id, 'characters', row['characters']))


# Function to insert tags from image_tags.csv
def insert_image_tags(csv_path):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        image_id = row['id']
        cursor.execute('''
        INSERT INTO image_tags (id, tags)
        VALUES (?, ?)
        ''', (image_id, row['tags']))


# Insert metadata and tags from CSV files
insert_image_metadata('dataset gatherer/nekos_api/image_metadata.csv')
insert_image_tags('dataset gatherer/nekos_moe/image_tags.csv')

# Commit changes and close the connection
conn.commit()
conn.close()
