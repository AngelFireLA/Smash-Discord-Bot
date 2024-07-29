import sqlite3
import os
import shutil

# Connect to the database
conn = sqlite3.connect('images.db')
cursor = conn.cursor()

# Create the 'smash' folder if it doesn't exist
if not os.path.exists('smash'):
    os.makedirs('smash')

# Query to select all images with the label 'smash'
query = "SELECT direct_path FROM images WHERE label = 'smash'"
cursor.execute(query)
smash_images = cursor.fetchall()
print(len(smash_images))

# Copy each image to the 'smash' folder
for image in smash_images:
    image_path = image[0]
    full_image_path = os.path.join('static', image_path)
    if os.path.exists(full_image_path):
        shutil.copy(full_image_path, 'smash')
    else:
        print(f"Image {full_image_path} not found")

# Close the database connection
conn.close()
