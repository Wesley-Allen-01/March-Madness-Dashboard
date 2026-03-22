"""Development entrypoint that mirrors `flask --app app run`."""

from app import app


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
