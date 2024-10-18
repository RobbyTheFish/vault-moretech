import uvicorn
from api.api import app
from loguru import logger


if __name__ == "__main__":
    # logger.remove()
    # logger.add(
    #     "logs/debug.log",
    #     format="[{time:YYYY-MM-DD HH:mm:ss}] {level} | {message}",
    #     level="TRACE",
    # )
    # logger.add(
    #     sys.__stdout__,
    #     format="[{time:YYYY-MM-DD HH:mm:ss}] {level} | {message}",
    #     level="TRACE",
    #     colorize=True,
    # )
    # Запуск приложения FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
