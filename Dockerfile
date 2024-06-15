## Use the official Python image from the Docker Hub
#FROM python:3.12
#
## Create a directory for the app
#RUN mkdir /fastapi-app
#
## Set the working directory in the container
#WORKDIR /fastapi-app
#
## Copy the requirements.txt file into the container
#COPY requirements.txt .
#
## Install the dependencies
#RUN pip install -r requirements.txt
#
## Copy the rest of the application code into the container
#COPY . .
#
#RUN chmod a+x docker/*.sh
#
## Set the PYTHONPATH environment variable
#ENV PYTHONPATH=/fastapi-app/src
#
## Set the working directory to /fastapi-app/src
##WORKDIR /fastapi-app/src
##
### Command to run the application
##CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000"]
FROM python:3.8

RUN mkdir /fastapi-app

WORKDIR /fastapi-app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

RUN alembic upgrade head

WORKDIR src

CMD gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000