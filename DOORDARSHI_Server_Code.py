from flask import Flask, request
from PIL import Image
import ollama
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return 'No image provided', 400

    image = request.files['image']
    path = f"received.jpg"
    image.save(path)

    # Run MoonDream model
    result = ollama.generate(
        model='moondream',
        prompt='Describe the image.',
        images=[path]
    )
    return result['response']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
