import uvicorn
from api.api import app

if __name__ == "__main__":
    # Запуск приложения FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
