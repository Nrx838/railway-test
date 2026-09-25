FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py coach.py exercises.json reactions.json ./
CMD ["python", "bot.py"]
