# Use the official Alpine Linux image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Copy the python script and the requirements file into the container
COPY pinterest-downloader.py pinterest-downloader.py
COPY requirements.txt requirements.txt

# Install the dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Command to run your Pinterest downloader script
CMD ["python", "pinterest-downloader.py","Your account url here"]
