from flask import Flask, request, render_template, jsonify
import sqlite3
import tensorflow as tf
import numpy as np
from PIL import Image
import os

app = Flask(__name__)

# Load models
model1 = tf.keras.models.load_model('efficient_continued.h5')
model2 = tf.keras.models.load_model('best_model_3.h5')

# Connect to database
conn = sqlite3.connect('images.db', check_same_thread=False)
cursor = conn.cursor()


def preprocess_image(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    image = image.resize((256, 256))
    image = np.array(image) / 255.0  # Normalize the image
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/next_image')
def next_image():
    image_type = request.args.get('image_type', 'normal')
    user = request.args.get('user')
    subdataset = request.args.get('subdataset', 'normal')
    min_ai_score = request.args.get('min_ai_score', type=float)
    max_ai_score = request.args.get('max_ai_score', type=float)
    print(min_ai_score, max_ai_score)

    query = 'SELECT direct_path FROM images WHERE '
    params = []

    if image_type == 'my_labeled' and user:
        query += 'labeled_by = ? '
        params.append(user)
    elif image_type == 'any_labeled' and user:
        query += 'labeled_by != ? AND labeled_by IS NOT NULL '
        params.append(user)
    else:  # Default to 'normal'
        query += 'label IS NULL '

    if subdataset != 'normal':
        query += 'AND folder_path LIKE ? '
        params.append(subdataset + '%')

    if min_ai_score is not None and max_ai_score is not None:
        query += 'AND ai_score BETWEEN ? AND ? '
        params.extend([min_ai_score, max_ai_score])
    elif min_ai_score is not None:
        query += 'AND ai_score >= ? '
        params.append(min_ai_score)
    elif max_ai_score is not None:
        query += 'AND ai_score <= ? '
        params.append(max_ai_score)

    query += 'ORDER BY RANDOM() LIMIT 1'

    cursor.execute(query, params)
    row = cursor.fetchone()

    if row:
        image_path = '/static/' + row[0]
        return jsonify({'image_path': image_path})
    else:
        return jsonify({'image_path': None})




@app.route('/label_image', methods=['POST'])
def label_image():
    data = request.get_json()
    image_path = data['image_path'].replace('/static/', '')
    label = data['label']
    user = data['user']

    cursor.execute('''
    UPDATE images SET label = ?, labeled_by = ? WHERE direct_path = ?
    ''', (label, user, image_path))
    conn.commit()
    return jsonify({'status': 'success'})


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    image_path = data['image_path'].replace('/static/', '')
    model_number = data['model_number']

    # Preprocess the image
    full_image_path = os.path.join('static', image_path)
    processed_image = preprocess_image(full_image_path)

    # Predict using the selected model
    if model_number == 1:
        prediction = model1.predict(processed_image)[0][0]
    elif model_number == 2:
        prediction = model2.predict(processed_image)[0][0]
    else:
        return jsonify({'error': 'Invalid model number'})

    label = "Smash" if prediction >= 0.5 else "Pass"
    confidence = f"{prediction * 100:.2f}%"

    return jsonify({'label': label, 'confidence': confidence})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=25565, debug=True)
