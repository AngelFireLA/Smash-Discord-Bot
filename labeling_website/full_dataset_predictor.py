import sqlite3
import tensorflow as tf
import numpy as np
from PIL import Image
import os

# Load model
model2 = tf.keras.models.load_model('best_model_3.h5')

# Connect to database
conn = sqlite3.connect('images.db')
cursor = conn.cursor()

# Function to preprocess images
def preprocess_image(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    image = image.resize((256, 256))
    image = np.array(image) / 255.0  # Normalize the image
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

# Function to check if ai_score is valid
def is_valid_score(score):
    try:
        score = float(score)
        return 0 <= score <= 1
    except ValueError:
        return False

# Fetch all images with invalid or no ai_score
cursor.execute('SELECT id, direct_path, ai_score FROM images')
images = cursor.fetchall()

total_images = len(images)
remaining_images = total_images
stop_trigger = False

try:
    for idx, (image_id, image_path, ai_score) in enumerate(images):
        remaining_images -= 1
        if (idx + 1) % 100 == 0:
            print(f"{remaining_images} images remaining to predict.")

        if stop_trigger:
            print("Stop trigger activated. Exiting loop.")
            break

        # Check if the ai_score is valid
        if ai_score is None or not is_valid_score(ai_score):
            try:
                # Preprocess the image
                full_image_path = os.path.join('static', image_path)
                processed_image = preprocess_image(full_image_path)

                # Predict using model 2
                prediction = float(f"{model2.predict(processed_image)[0][0]:.2f}")
                # Update the ai_score in the database
                cursor.execute('''
                UPDATE images
                SET ai_score = ?
                WHERE id = ?
                ''', (round(prediction, 4), image_id))

                # Decrement the remaining images counter


            except Exception as e:
                print(f"Error processing image {image_path}: {e}")

except KeyboardInterrupt:
    print("Interrupted by user. Exiting loop.")

# Commit changes and close the connection
conn.commit()
conn.close()
