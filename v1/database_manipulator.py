





# # Cleans characters file

# import pandas as pd
#
# # Specify the filename
# filename = "anime_characters_edited"

# # Load the data
# data = pd.read_csv(filename)
#
# # Remove lines with duplicated Character Name
# data = data.drop_duplicates(subset="Character Name", keep="first")
#
# # Remove content within parentheses in all columns
# data = data.replace(to_replace=r'\(.*?(?=\,|\Z)', value='', regex=True)
#
# data["Hair Color"] = data["Hair Color"].str.replace("Blonde / Yellow", "Blonde")
#
# # Remove lines where Gender is Male or (Male)
# data = data[data["Gender"].str.strip().str.lower() != "male"]
#
# data = data.apply(lambda x: ','.join(x.split(',')[:12]), axis=1)
#
#
# # Write the data back to the CSV file
# data.to_csv(filename, index=False)


# # Remove commas

# def remove_after_12th_comma(line):
#     parts = line.split(',')
#     if len(parts) > 12:
#         return ','.join(parts[:13]) + '\n'
#     else:
#         return line
#
# def main():
#
#     try:
#         with open(filename+".csv", 'r') as input_file, open(filename + "_modified.csv", 'w') as output_file:
#             i=0
#             for line in input_file:
#                 i+=1
#                 print(i)
#                 modified_line = remove_after_12th_comma(line)
#                 output_file.write(modified_line)
#
#         print("Processing complete. Modified lines saved.")
#     except FileNotFoundError:
#         print("File not found. Please check the file path.")
#     except Exception as e:
#         print("An error occurred:", str(e))
#
# if __name__ == "__main__":
#     main()


# # creates the databse

# import sqlite3
#
# # Create a connection to the database
# conn = sqlite3.connect('anime.db')
#
# # Create a cursor object
# c = conn.cursor()
#
# # Create the users table
# c.execute('''
#     CREATE TABLE users(
#         id INTEGER PRIMARY KEY,
#         username TEXT)
# ''')
#
# # Create the characters table
# c.execute('''
#     CREATE TABLE characters(
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         height TEXT,
#         weight TEXT,
#         bust TEXT,
#         waist TEXT,
#         hip TEXT,
#         gender TEXT,
#         eye_color TEXT,
#         hair_color TEXT,
#         hair_length TEXT,
#         apparent_age TEXT,
#         animal_ears TEXT
#         )
# ''')
#
# # Create the liked characters table
# c.execute('''
#     CREATE TABLE liked_characters(
#         user_id INTEGER,
#         character_id INTEGER,
#         liked_on DATETIME,
#         FOREIGN KEY(user_id) REFERENCES users(id),
#         FOREIGN KEY(character_id) REFERENCES characters(id))
# ''')
#
# # Insert a user
# c.execute('''
#     INSERT INTO users(username) VALUES(?)
# ''', ('username1',))
#
# # Commit the changes
# conn.commit()

import pandas as pd
import sqlite3

# Read the CSV file
df = pd.read_csv('csv_files/anime_characters_edited.csv')

# Connect to the SQLite database
conn = sqlite3.connect('anime.db')
c = conn.cursor()

# Create the characters table if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS characters(
        id INTEGER PRIMARY KEY,
        name TEXT,
        height TEXT,
        weight TEXT,
        bust TEXT,
        waist TEXT,
        hip TEXT,
        gender TEXT,
        eye_color TEXT,
        hair_color TEXT,
        hair_length TEXT,
        apparent_age TEXT,
        animal_ears TEXT
    )
''')

# Function to insert a character into the database
def insert_character(row):
    c.execute('''
        INSERT INTO characters(name, height, weight, bust, waist, hip, gender, eye_color, hair_color, hair_length, apparent_age, animal_ears) 
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (row['Character Name'], row['Height'], row['Weight'], row['Bust'], row['Waist'], row['Hip'], row['Gender'], row['Eye Color'], row['Hair Color'], row['Hair Length'], row['Apparent Age'], row['Animal Ears']))

# Iterate over the DataFrame and insert each character
df.apply(insert_character, axis=1)

# Commit the changes and close the connection
conn.commit()
conn.close()







