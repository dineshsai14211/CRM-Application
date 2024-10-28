# Stage 1: Builder
FROM python:3.9-slim AS builder

# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /main

# Copy the requirements file to the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Stage 2: Run
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /main

# Copy only the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /main /main

# Expose the port the app runs on
EXPOSE 5000

# Set the PYTHONPATH environment variable to include /main
ENV PYTHONPATH="${PYTHONPATH}:/main"

# Run the application
CMD ["python", "apps/app.py"]


