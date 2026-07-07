# docker/Dockerfile.app
# =====================
# Streamlit frontend container
# Owner: Hung
#
# Build:   docker build -f docker/Dockerfile.app -t bs4-app .
# Run:     docker run -p 8501:8501 -e API_BASE_URL=http://api:8000 bs4-app

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source 
COPY shared/        ./shared/
COPY app/           ./app/
COPY conftest.py    .

EXPOSE 8501

# Disable Streamlit's browser auto-open and telemetry in container
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
