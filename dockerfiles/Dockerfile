FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements trước để tận dụng cache
COPY app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code (đặt nguyên thư mục app/ vào /app/app)
COPY app/ /app/app

# Expose port
EXPOSE 8000

