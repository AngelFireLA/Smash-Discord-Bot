import tensorflow as tf
import numpy as np



# Load the training data
train_images = np.load('dataset_npy/train_images.npy')
train_labels = np.load('dataset_npy/train_labels.npy')
# Load the validation data
val_images = np.load('dataset_npy/val_images.npy')
val_labels = np.load('dataset_npy/val_labels.npy')

# Load the trained model
model = tf.keras.models.load_model('efficient_2_20_20.h5')
# Evaluate the model on the validation data
loss, accuracy = model.evaluate(val_images, val_labels)
print('efficient_2_20_20.h5')
print(f'Validation Loss: {loss}')
print(f'Validation Accuracy: {accuracy}')

name = "efficient_continued.h5"
# Load the trained model
model = tf.keras.models.load_model(name)
# Evaluate the model on the validation data
loss, accuracy = model.evaluate(val_images, val_labels)
print(name)
print(f'Validation Loss: {loss}')
print(f'Validation Accuracy: {accuracy}')

name = "efficient_continued2.h5"
# Load the trained model
model = tf.keras.models.load_model(name)
# Evaluate the model on the validation data
loss, accuracy = model.evaluate(val_images, val_labels)
print(name)
print(f'Validation Loss: {loss}')
print(f'Validation Accuracy: {accuracy}')

name = "best_model_3.h5"
# Load the trained model
model = tf.keras.models.load_model(name)
# Evaluate the model on the validation data
loss, accuracy = model.evaluate(val_images, val_labels)
print(name)
print(f'Validation Loss: {loss}')
print(f'Validation Accuracy: {accuracy}')
