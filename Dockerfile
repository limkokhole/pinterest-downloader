FROM ubuntu:latest

# Install dependencies
RUN apt-get update && \
    apt-get install -y git python3 python3-pip chromium-driver

# Clone the repository
RUN git clone https://github.com/raven2cz/pinterest-downloader.git

# Set working directory
WORKDIR /pinterest-downloader

# Install Python requirements
RUN pip3 install -r requirements.txt --break-system-packages

# Keep the container running
CMD ["tail", "-f", "/dev/null"]
