FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements trước để tận dụng cache
COPY app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ /app/app

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
