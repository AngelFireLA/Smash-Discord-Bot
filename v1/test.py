import asyncio
import math
import aiosqlite
import re
import re
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from heapq import nlargest

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


def convert_character_to_dict(character_info):
    c_id, name, height, weight, bust, waist, hip, gender, eye_color, hair_color, hair_length, apparent_age, animal_ears = character_info

    character =  {'id': c_id, 'name': name, 'Height': extract_number(height), 'Weight': extract_number(weight), 'Bust': extract_number(bust), 'Waist': extract_number(waist), 'Hip': extract_number(hip),
            'Gender': gender, 'Eye Color': eye_color, 'Hair Color': hair_color, 'Hair Length': hair_length,
            'Apparent Age': apparent_age, 'Animal Ears': animal_ears}
    character_with_attributes_as_numbers = {k: characteristics_dict[k][v] if k in characteristics_dict else v for k, v
                                            in character.items()}

    return character_with_attributes_as_numbers





async def get_liked_characters(user_id):
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Execute an SQL query to fetch all characters liked by the user
            await c.execute(
                'SELECT characters.* FROM characters JOIN liked_characters ON characters.id = liked_characters.character_id WHERE liked_characters.user_id = ?',
                (user_id,))
            liked_characters = await c.fetchall()

    return liked_characters


async def get_all_characters():
    # Connect to the SQLite database
    async with aiosqlite.connect('anime.db') as conn:
        async with conn.cursor() as c:
            # Execute an SQL query to fetch all characters
            await c.execute('SELECT * FROM characters')
            all_characters = await c.fetchall()

    # Return all characters
    return all_characters


def int_to_string(characteristic, value):
    for key, val_dict in characteristics_dict.items():
        if key == characteristic:
            for string_val, int_val in val_dict.items():
                if int_val == value:
                    return string_val
    return None

def convert_character_to_strings(character):
    converted_character = {}
    for key, value in character.items():
        if key in characteristics_dict:
            converted_value = int_to_string(key, value)
            if converted_value is not None:
                converted_character[key] = converted_value
        else:
            converted_character[key] = value
    return converted_character


async def main():
    user_id = 554717217720369163  # Replace with the actual user ID
    k = 3

    # Retrieve the liked characters for the user
    liked_characters = await get_liked_characters(user_id)

    # Retrieve all characters
    all_characters = await get_all_characters()

    # Convert characters to feature vectors
    liked_feature_vectors = [list(convert_character_to_dict(char).values())[2:] for char in liked_characters]
    all_feature_vectors = [list(convert_character_to_dict(char).values())[2:] for char in all_characters]

    # Convert lists of feature vectors to numpy arrays
    liked_feature_array = np.array(liked_feature_vectors)
    all_feature_array = np.array(all_feature_vectors)

    # Create an imputer object that uses the mean imputation method
    from sklearn.impute import SimpleImputer
    imputer = SimpleImputer(strategy='mean')

    # Apply the imputer to the feature arrays
    liked_feature_array = imputer.fit_transform(liked_feature_array)
    all_feature_array = imputer.transform(all_feature_array)

    # Calculate cosine similarities
    similarities = cosine_similarity(all_feature_array, liked_feature_array)

    # Find the top-k characters with the highest cosine similarities that are not in the liked characters
    suggestions = []
    for i, character in enumerate(all_characters):
        if character not in liked_characters:
            similarity = np.max(similarities[i])  # Get the highest similarity with any liked character
            suggestions.append((character, similarity))

    top_k_suggestions = nlargest(k, suggestions, key=lambda x: x[1])  # Get the top-k suggestions based on similarity

    # Print the suggestions
    if top_k_suggestions:
        print("Suggestions:")
        for suggestion in top_k_suggestions:
            print(f"- {suggestion[0][0]}")  # Index 1 for 'name'
    else:
        print("No suggestions found.")



    # Perform Singular Value Decomposition (SVD)
    from sklearn.decomposition import TruncatedSVD

    # Perform Singular Value Decomposition (SVD)
    svd = TruncatedSVD(n_components=liked_feature_array.shape[1])  # Adjust n_components to the number of features
    liked_feature_array_svd = svd.fit_transform(liked_feature_array)
    all_feature_array_svd = svd.transform(all_feature_array)

    # Calculate recommendations based on similarity with latent factors
    similarity_scores = np.dot(all_feature_array_svd, liked_feature_array_svd.T)
    sorted_indices = np.argsort(similarity_scores, axis=0)[::-1]  # Sort characters based on similarity scores

    # Filter and print the top-k recommendations that are not in the liked characters list
    recommendations = []
    for i in range(all_feature_array.shape[0]):
        if all_characters[i] not in liked_characters:
            recommendations.append(all_characters[sorted_indices[i][0]])

        if len(recommendations) >= k:
            break

    # Print the recommendations
    if recommendations:
        print("Recommendations:")
        for recommendation in recommendations:
            print(f"- {recommendation}")
    else:
        print("No recommendations found.")

# Run the main function
asyncio.run(main())




