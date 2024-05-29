from flask import Flask, render_template, request, redirect, url_for
import os
from duplicates_dict import duplicates  # Import the generated duplicates dictionary

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', duplicates=duplicates)

@app.route('/delete', methods=['POST'])
def delete():
    file_to_delete = request.form['file_to_delete']
    file_path = os.path.join('static', file_to_delete.replace("\\", "/"))
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))

@app.route('/keep', methods=['POST'])
def keep():
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
