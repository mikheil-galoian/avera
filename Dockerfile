FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies only (no system packages needed)
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY demo/ ./demo/
COPY fixtures/ ./fixtures/
COPY reports/ ./reports/
COPY deploy/ ./deploy/
COPY pyproject.toml .

# Install AVERA package (no extras, no C extensions)
RUN pip install --no-cache-dir -e "." --no-build-isolation

ENV PYTHONPATH=/app/src
ENV AVERA_DEFAULT_SCENARIO=bms-fast-charge

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "demo/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
