# Use an official Python runtime as a parent image
FROM python

# Set the working directory in the container
WORKDIR /main

# Copy the requirements file to the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
