FROM python:3.12
WORKDIR /app
COPY Requirements/requirements-ui.txt .
RUN pip install --no-cache-dir -r requirements-ui.txt
COPY UI/ ./UI
EXPOSE 8501
CMD ["streamlit", "run", "UI/app_rain.py"]