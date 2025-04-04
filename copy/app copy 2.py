from flask import Flask, request, render_template_string
import requests
import re
import html

API_KEY = "AIzaSyDqwy_Mq7Ilc-VBq2C9jLxrChFizpypQlk"
CX = "f357e9409629e47cd"

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Проверка уникальности текста</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; }
        textarea, .editable-result { width: 100%; font-size: 14px; border: 1px solid #ccc; padding: 10px; border-radius: 5px; background: #fff; }
        textarea { height: 200px; }
        .editable-result { white-space: pre-wrap; min-height: 200px; }
        .result { margin-top: 20px; background: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 0 5px rgba(0,0,0,0.1); }
        .match { margin-bottom: 10px; }
        .snippet { font-size: 13px; color: #555; }
        .highlight { background-color: yellow; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Проверка уникальности текста</h1>
    <form method="post">
        <textarea name="text">{{ text or '' }}</textarea><br>
        {% if highlighted_text %}
            <p><strong>Совпадающие слова подсвечены ниже:</strong></p>
            <div class="editable-result">{{ highlighted_text|safe }}</div>
        {% endif %}
        <button type="submit">Проверить</button>
    </form>
    {% if uniqueness is not none %}
    <div class="result">
        <h2>Уникальность: {{ uniqueness }}%</h2>
        {% if matches %}
        <h3>Найдено совпадений: {{ matches|length }}</h3>
        <ul>
            {% for match in matches %}
            <li class="match">
                <a href="{{ match.link }}" target="_blank">{{ match.link }}</a><br>
                <span class="snippet">{{ match.highlighted_snippet|safe }}</span>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p>Совпадений не найдено.</p>
        {% endif %}
    </div>
    {% endif %}
</body>
</html>
"""

def google_search(query, num_results=5):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CX,
        "num": num_results
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []

    items = response.json().get("items", [])
    results = []

    for item in items:
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        results.append({"link": link, "snippet": snippet})

    return results

def highlight_matches(snippet, words):
    safe_snippet = html.escape(snippet)
    for word in words:
        word_escaped = re.escape(word)
        safe_snippet = re.sub(
            rf"(?i)(?<!\w|[«\"'“”])({word_escaped})(?!\w|[.,!?;:»\"'“”])",
            r"<span class='highlight'>\1</span>",
            safe_snippet
        )
    return safe_snippet

def highlight_text_input(text, repeated_words, matched_fragments=None):
    def mark_words(raw_text, words):
        for word in set(words):
            word_escaped = re.escape(word)
            raw_text = re.sub(
                rf"(?i)(?<!\w|[.«\"'“”])({word_escaped})(?!\w|[.,!?;:»\"'“”])",
                r"<span class='highlight'>\1</span>",
                raw_text
            )
        return raw_text

    def mark_fragments(raw_text, fragments):
        for fragment in fragments:
            fragment = fragment.strip()
            if len(fragment) < 5:
                continue
            fragment_escaped = re.escape(fragment)
            raw_text = re.sub(
                fragment_escaped,
                lambda m: f"<span class='highlight'>{m.group(0)}</span>",
                raw_text,
                flags=re.IGNORECASE
            )
        return raw_text

    # сначала подсветим слова и фрагменты на "сыром" тексте
    marked_text = text
    if repeated_words:
        marked_text = mark_words(marked_text, repeated_words)
    if matched_fragments:
        marked_text = mark_fragments(marked_text, matched_fragments)

    # потом экранируем HTML, но оставим <span> нетронутыми
    def safe_html(text_with_tags):
        parts = re.split(r'(<span.*?>.*?</span>)', text_with_tags, flags=re.IGNORECASE)
        return ''.join([
            html.escape(part) if not part.startswith('<span') else part
            for part in parts
        ])

    return safe_html(marked_text)

def check_text_uniqueness(text):
    paragraphs = re.split(r'\n{2,}|\n', text)
    paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 10]

    all_matches = []
    all_repeated_words = []

    for paragraph in paragraphs:
        paragraph_words = paragraph.lower().split()
        results = google_search(paragraph)
        for res in results:
            snippet_lower = res["snippet"].lower()
            if any(word in snippet_lower for word in paragraph_words):
                highlighted_snippet = highlight_matches(res["snippet"], paragraph_words)
                all_matches.append({
                    "link": res["link"],
                    "snippet": res["snippet"],
                    "highlighted_snippet": highlighted_snippet
                })
                for word in paragraph_words:
                    if word in snippet_lower:
                        all_repeated_words.append(word)

    total_paragraphs = len(paragraphs) or 1
    uniqueness = max(0, 100 - int((len(all_matches) / total_paragraphs) * 100))

    matched_fragments = [match["snippet"] for match in all_matches]
    highlighted_text = highlight_text_input(text, all_repeated_words, matched_fragments)

    return uniqueness, all_matches, highlighted_text

@app.route("/", methods=["GET", "POST"])
def index():
    text = ""
    uniqueness = None
    matches = []
    highlighted_text = None

    if request.method == "POST":
        text = request.form["text"]
        uniqueness, matches, highlighted_text = check_text_uniqueness(text)

    return render_template_string(
        HTML_TEMPLATE,
        text=text,
        uniqueness=uniqueness,
        matches=matches,
        highlighted_text=highlighted_text
    )

if __name__ == "__main__":
    app.run(debug=False)
