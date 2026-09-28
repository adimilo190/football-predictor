# app/prediction/__init__.py
# Marks app/prediction/ as a package. The package holds the prediction model and
# nothing else: poisson.py is pure maths (numbers in, numbers out) and strength.py
# turns stored standings into the expected goals that maths needs. Neither file
# knows anything about FastAPI or HTTP - the endpoint in routers/predictions.py
# wires them together. That separation keeps the model testable on its own.
