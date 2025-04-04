from flask import Flask, request, render_template, jsonify
import requests
import time

app = Flask(__name__)

API_KEY = 'AIzaSyDqwy_Mq7Ilc-VBq2C9jLxrChFizpypQlk'
CX = 'f357e9409629e47cd'
SEARCH_URL = 'https://www.googleapis.com/customsearch/v1'

def check_uniqueness(text):
    phrases = [phrase.strip() for phrase in text.split('.') if phrase.strip()]
    results = []

    for phrase in phrases:
        params = {
            'key': API_KEY,
            'cx': CX,
            'q': f'"{phrase}"'  # Точное совпадение
        }
        response = requests.get(SEARCH_URL, params=params)
        data = response.json()
        count = int(data.get('searchInformation', {}).get('totalResults', 0))
        results.append({'phrase': phrase, 'results': count})
        time.sleep(1)  # Не спамим Google

    total = len(phrases)
    unique = sum(1 for r in results if r['results'] == 0)
    uniqueness_percent = round((unique / total) * 100, 2)

    return {
        'uniqueness': uniqueness_percent,
        'details': results
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    text = request.json.get('text', '')
    result = check_uniqueness(text)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
