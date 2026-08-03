# Makes `tests` a package. Side effect we rely on: pytest then inserts the
# project root into sys.path, so `from app.main import app` works from the tests.
