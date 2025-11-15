"""Entry point for the Dynamic ETL Pipeline project."""

from api.routes import create_app

# Create app instance at module level for uvicorn
app = create_app()


def main():
    """Initialize the API application.

    Returns
    -------
    Any
        The instantiated API application (framework-agnostic placeholder).
    """
    return app


if __name__ == "__main__":
    main()
