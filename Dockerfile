FROM python:3.13
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR code/
COPY Pipfile Pipfile.lock ./
RUN python -m pip install pipenv && pipenv install --system
COPY . .
CMD "python manage.py runserver 0.0.0.0:8000"
EXPOSE 8000