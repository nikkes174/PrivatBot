# PrivatBot — Telegram Bot + FastAPI + Robokassa

**Telegram-бот и веб-сервис** для продажи подписок на приватный канал через Robokassa.  
Пользователь может оформить подписку, оплатить онлайн, получить автоматический доступ в закрытый канал, а также управлять автопродлением.

---

## ✨ Основные возможности

- 🤖 **Telegram-бот (Aiogram 3)**
  - приветственное меню
  - inline-кнопки (подписки, оферта, отмена автопродления)
  - автоматическая выдача доступа в канал после оплаты
  - поддержка рекуррентных платежей (автопродление)

- 🌐 **FastAPI веб-приложение**
  - обработка колбэков Robokassa (`/result`, `/success`, `/fail`)
  - валидация подписи платежа
  - интеграция с PostgreSQL (хранение подписок)

- 💳 **Robokassa интеграция**
  - разовые платежи
  - рекуррентные (автосписания) 

- 🗄 **База данных (PostgreSQL)**
  - таблица `privat_user` со сроками подписки
  - автопродление через планировщик
  - очистка пользователей с истёкшей подпиской

---

## ⚙️ Технологии

- [Python 3.11+](https://www.python.org/)  
- [Aiogram 3](https://docs.aiogram.dev/en/latest/) — Telegram Bot API  
- [FastAPI](https://fastapi.tiangolo.com/) — backend для колбэков Robokassa  
- [PostgreSQL](https://www.postgresql.org/) + [asyncpg](https://github.com/MagicStack/asyncpg)  
- [Robokassa](https://robokassa.com/) — приём платежей  
- [Docker](https://www.docker.com/) — деплой (опционально)

---

## 📂 Структура проекта

```text
project/
│── app.py                 # FastAPI сервер (колбэки Robokassa)
│── database.py            # Работа с PostgreSQL (подписки)
│── tgbot/
│   ├── handlers/          # Хэндлеры бота
│   │   └── user.py
│   │
│   ├── keyboards/         # Inline-кнопки
│   │   └── inline.py
│   │
│   ├── middlewares/       # Config / DB middlewares
│   │   └── config.py
│   │   └── database.py
│   │
│   ├── misc/              # FSM состояния
│   │   └── states.py
│   │
│   ├── services/          # Бизнес-логика
│   │   └── payment.py     # Логика Robokassa
│   │   └── config.py      # (если выносишь загрузку env)
│   │
│   └── __init__.py
│
│── requirements.txt       # Зависимости
│── .env.example           # Пример настроек окружения
│── README.md              # Документация проекта


