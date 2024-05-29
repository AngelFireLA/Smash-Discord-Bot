import sqlite3
import numpy as np
import tensorflow as tf
from PIL import Image
import matplotlib.pyplot as plt

def get_random_image():
    # Connect to the SQLite database
    conn = sqlite3.connect('images.db', check_same_thread=False)
    cursor = conn.cursor()

    # Fetch an image path from the database
    cursor.execute('''
    SELECT direct_path FROM images WHERE label IS NULL ORDER BY RANDOM() LIMIT 1
    ''')
    row = cursor.fetchone()
    image_path = row[0]

    # Close the database connection
    conn.close()

    return image_path

# Function to preprocess the input image
def preprocess_image(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    image = image.resize((256, 256))
    image = np.array(image) / 255.0  # Normalize the image
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

print("loading")
model_names = ['best_model_4.h5',
               'best_model_3.h5'
               ]

models = [tf.keras.models.load_model(name) for name in model_names]

while True:
    image_path = get_random_image()
    # Preprocess the image
    processed_image = preprocess_image(image_path)

    print("predicting")
    predictions = [model.predict(processed_image) for model in models]

    print("predicted")

    confidence = [prediction[0][0] for prediction in predictions]
    # Determine the labels and confidences
    labels = ["Smash" if prediction[0] > 0.5 else "Pass" for prediction in predictions]

    # Display the image with labels and confidences
    image = Image.open(image_path)
    plt.figure()
    plt.imshow(image)
    plt.axis('off')

    plt_title = ""
    for i in range(len(labels)):
        plt_title += f"Model {i}: {labels[i]} ({confidence[i]:.2f})\n"

    print(plt_title)
    plt.figtext(0.5, 0.01, plt_title, ha="center", fontsize=12, wrap=True)
    plt.show()