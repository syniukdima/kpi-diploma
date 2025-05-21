from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Додавання шляху до спільних модулів
sys.path.append(os.path.abspath(".."))

app = FastAPI(title="Мікросервіс Групування API", 
             description="API для групування мікросервісів на основі метрик навантаження",
             version="1.0.0")

# Налаштування CORS для взаємодії з фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Дозволяємо тільки фронтенд на localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Мікросервіс Групування API працює"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Підключення маршрутів API
from app.api.routes import router
app.include_router(router, prefix="/api")

# Запуск серверу при виконанні цього файлу напряму
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 