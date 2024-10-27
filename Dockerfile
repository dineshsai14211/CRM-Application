# Stage 1: Build
FROM python:latest AS builder

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
COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=builder /main /main

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "apps/app.py"]
