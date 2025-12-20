# Uses one of Playwright official images to handle all browser needed deps
FROM mcr.microsoft.com/playwright/python:3.11

# Sets an environmental variable to prevent Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Sets an environmental variable to prevent Python from buffering outputs
ENV PYTHONUNBUFFERED=1

# Install basic dependencies
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Sets workdir
WORKDIR /discord-bot

# Copy project requirement file and install them
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Installs Playwright browsers
RUN playwright install

# Copy other project files
COPY . .

# Defines the command to run the bot when the conteiner starts
CMD ["python", "src/main.py"]