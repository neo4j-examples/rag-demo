FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "rag_demo/main.py", "--server.enableCORS", "false", "--browser.serverAddress", "0.0.0.0", "--browser.gatherUsageStats", "false", "--server.port", "8080"]