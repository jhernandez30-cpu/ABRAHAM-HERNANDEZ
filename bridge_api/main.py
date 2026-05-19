from app import create_app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    from app.config import settings

    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())
