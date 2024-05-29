import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import sqlite3
import pandas as pd

# Define the base path where your dataset is stored
base_path = 'dataset gatherer'

# Define the target image size
IMG_SIZE = (256, 256)

# Initialize lists to hold file paths and labels
file_paths = []
labels = []

# Function to traverse directories and collect image paths
def collect_image_paths(base_path):
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(('jpg', 'jpeg', 'png', 'gif')):
                file_path = os.path.join(root, file)
                file_id, _ = os.path.splitext(file)
                file_paths.append((file_id, file_path))

# Collect all image paths
collect_image_paths(base_path)

# Connect to the SQLite database
conn = sqlite3.connect('images.db')
cursor = conn.cursor()

# Fetch labels from the database
def fetch_labels(file_id):
    # Only fetch label if it is not delete
    cursor.execute('SELECT label FROM images WHERE id = ? AND label != "delete"', (file_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# Map file paths to labels
for file_id, file_path in file_paths:
    label = fetch_labels(file_id)
    if label:  # Only add if a label exists
        labels.append(label)
        file_paths[file_paths.index((file_id, file_path))] = file_path

# Convert lists to numpy arrays
file_paths = [path for path in file_paths if isinstance(path, str)]
labels = np.array(labels)

# Convert labels to integers
label_mapping = {'smash': 1, 'pass': 0}
labels = np.array([label_mapping[label] for label in labels])

# Split data into training and validation sets
train_paths, val_paths, train_labels, val_labels = train_test_split(file_paths, labels, test_size=0.2, random_state=42)

# Number of images in each dataset
num_train_images = len(train_paths)
num_val_images = len(val_paths)

print(f'Number of training images: {num_train_images}')
print(f'Number of validation images: {num_val_images}')

# Function to preprocess images
def preprocess_image(image_path):
    try:
        image = Image.open(image_path)
        image = image.convert("RGB")
    except Exception as e:
        print(image_path)
        raise e
    # Resize image while maintaining aspect ratio
    image.thumbnail(IMG_SIZE, Image.LANCZOS)
    # Create a new image with a white background
    new_image = Image.new("RGB", IMG_SIZE, (255, 255, 255))
    new_image.paste(image, ((IMG_SIZE[0] - image.size[0]) // 2, (IMG_SIZE[1] - image.size[1]) // 2))
    # Normalize pixel values
    new_image = np.array(new_image) / 255.0
    return new_image

# Preprocess and save training images
train_images = np.array([preprocess_image(path) for path in train_paths]).astype('float32')
val_images = np.array([preprocess_image(path) for path in val_paths]).astype('float32')

# Number of images in each dataset after preprocessing
num_train_images_processed = len(train_images)
num_val_images_processed = len(val_images)

print(f'Number of preprocessed training images: {num_train_images_processed}')
print(f'Number of preprocessed validation images: {num_val_images_processed}')

# Data augmentation
train_datagen = ImageDataGenerator(
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.2
)

val_datagen = ImageDataGenerator()

train_generator = train_datagen.flow(train_images, train_labels, batch_size=64)
val_generator = val_datagen.flow(val_images, val_labels, batch_size=64)

# Number of batches per epoch
num_train_batches = len(train_generator)
num_val_batches = len(val_generator)

print(f'Number of batches per epoch in training: {num_train_batches}')
print(f'Number of batches per epoch in validation: {num_val_batches}')

# Save the preprocessed data (optional)
np.save('train_images3.npy', train_images)
np.save('train_labels3.npy', train_labels)
np.save('val_images3.npy', val_images)
np.save('val_labels3.npy', val_labels)

# Close the database connection
conn.close()
