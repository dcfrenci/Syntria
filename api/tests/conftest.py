import os

os.environ.update(
    {
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "t" * 16,
        "POSTGRES_DB": "test",
        "POSTGRES_HOST": "localhost",
        "SECRET_KEY": "k" * 40,
        "ADMIN_EMAIL": "admin@example.test",
    }
)
