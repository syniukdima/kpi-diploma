from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

# Додавання шляху до спільних модулів
sys.path.append(os.path.abspath(".."))

app = FastAPI(title="Мікросервіс Групування API", 
             description="API для групування мікросервісів на основі метрик навантаження",
             version="1.0.0")

# Налаштування CORS для взаємодії з фронтендом
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    # Продакшн налаштування - дозволяємо тільки твій домен
    allowed_origins = [
        "https://syniukdmytro.online",  # Замінити на твій домен
        "https://www.syniukdmytro.online",  # Замінити на твій домен
    ]
else:
    # Розробка - дозволяємо localhost
    allowed_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Мікросервіс Групування API працює", "environment": environment}

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": environment}

# Підключення маршрутів API
from app.api.routes import router
app.include_router(router, prefix="/api")

# Запуск серверу при виконанні цього файлу напряму
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)