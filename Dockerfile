FROM python:3.13
WORKDIR code/
COPY Pipfile Pipfile.lock ./
RUN python -m pip install pipenv && pipenv install --system
COPY . .
CMD "python manage.py runserver 0.0.0.0:8000"
EXPOSE 8000