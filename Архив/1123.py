import requests

# URL вебхука, который вы получили от Discord
webhook_url = "https://discord.com/api/v9/channels/1000480372213170306/messages"

# Заголовки, которые вы хотите использовать (не обязательно, но могут потребоваться в некоторых случаях)
headers = {
    "Content-Type": "application/json",
    "Authorization": "tokin😋"
}

# Данные, которые будут отправлены в виде сообщения
data = {
  "mobile_network_type": "unknown",
  "content": "👍",
  "flags": 0,
  "has_poggermode_enabled": True,
  "content_inventory_entry": {
    "unverified_content": {
      "id": "1279338022541725697",
      "author_id": "842305354322542592",
      "author_type": 1,
      "content_type": 1,
      "traits": [
        {
          "type": 3,
          "is_live": True
        },
        {
          "type": 8,
          "streak_count_days": 15
        },
        {
          "type": 6,
          "marathon": True
        },
        {
          "type": 2,
          "duration_seconds": 19795
        }
      ],
      "extra": {
        "type": "played_game_extra",
        "game_name": "STALCRAFT",
        "application_id": "1124351909235539978",
        "platform": 0
      },
      "participants": [
        "842305354322542592"
      ],
      "started_at": "2024-08-31T07:12:33.525000+00:00",
      "signature": {
        "signature": "b8a7d8a375d8f673356d6144af5eb2e8754d84e570d1fe0a6004063f9ab2f7e5",
        "kid": "AtDT4Kx25Wmu5cfllPxAiwZKgPbmLsaeHitpx/duvPY=",
        "version": 1
      }
    }
  }
}

# Отправка POST-запроса к вебхуку
response = requests.post(webhook_url, json=data, headers=headers)

# Проверка успешности запроса
if response.status_code == 204:
    print("Сообщение успешно отправлено в канал Discord!")
else:
    print(f"Ошибка при отправке сообщения: {response.status_code} - {response.text}")
