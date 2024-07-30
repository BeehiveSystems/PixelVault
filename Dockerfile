FROM python:3.9-slim

# Set the working directory
WORKDIR /usr/src/app

# Install dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available outside this container
EXPOSE 5000

# Run app.py when the container launches
#CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
CMD ["gunicorn", "--log-level", "debug", "--error-logfile", "-", "-b", "0.0.0.0:5000", "app:app"]
