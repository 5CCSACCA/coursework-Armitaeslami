# using simple python image
FROM python:3.10-slim

# install system packages required by OpenCV and Ultralytics
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

# main folder inside container
WORKDIR /app

# install python packages
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy project files
COPY . .

# run main.py when container starts
CMD ["python", "app/main.py"]
