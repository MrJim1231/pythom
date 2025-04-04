import requests
import re

API_KEY = "AIzaSyDgZu3Whd4bbHzGNHBhykXtgJ1nLyyOLuU"
CX = "32819015c0f5f47d7"  # Ваш CX

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
        print("Ошибка при запросе в Google:", response.json())
        return []

    results = response.json().get("items", [])
    return [item.get("link", "") for item in results]

def check_text_uniqueness(text):
    # Разбиваем по строкам (включая списки фильмов)
    lines = text.split('\n')
    lines = [line.strip() for line in lines if len(line.strip()) > 5]

    duplicate_sources = set()
    total_checks = 0

    for line in lines:
        results = google_search(line)
        if results:
            duplicate_sources.update(results)
        total_checks += 1

    # Чем больше дубликатов — тем ниже уникальность
    if total_checks == 0:
        return 100, set()

    ratio = len(duplicate_sources) / total_checks
    uniqueness = max(0, int((1 - ratio) * 100))

    return uniqueness, duplicate_sources

if __name__ == "__main__":
    user_text = """Вот наш топ-10:
    Дневник памяти (2004)
    Один день (2011)
    Мой король (2015)
    Любовники (2008)
    Вечное сияние чистого разума (2004)
    Гордость и предубеждение (2005)
    500 дней лета (2009)
    Амели (2001)"""

    uniqueness, sources = check_text_uniqueness(user_text)

    print(f"Уникальность текста: {uniqueness}%")
    if sources:
        print("Обнаружены совпадения на следующих сайтах:")
        for source in sources:
            print(source)
