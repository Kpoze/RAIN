FROM python:3.12
WORKDIR /app
COPY Requirements/requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt
COPY UI/ ./UI
EXPOSE 8501
CMD ["streamlit", "run", "UI/app_rain.py"]