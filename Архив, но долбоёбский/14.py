import cloudscraper

scraper = cloudscraper.create_scraper()  # Имитация запроса с браузера
response = scraper.get('https://aternos.org/hermes')
print(response.text)  # Должен вернуть корректную страницу или токен
