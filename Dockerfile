FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (including .env, templates, static)
COPY . .

# Flask will read .env automatically (thanks to python-dotenv)
ENV FLASK_APP=app.py

# Expose the port defined in .env (default 8888)
EXPOSE 8888

# Run Flask using .env settings
CMD ["flask", "run", "--host=0.0.0.0"]