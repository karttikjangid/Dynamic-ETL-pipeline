"""Entry point for the Dynamic ETL Pipeline project."""

from api.routes import create_app


def main():
    """Initialize the API application.

    Returns
    -------
    Any
        The instantiated API application (framework-agnostic placeholder).
    """

    app = create_app()
    return app


if __name__ == "__main__":
    main()
