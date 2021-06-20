FROM continuumio/miniconda:latest

# Install tesseract
RUN apt-get update \
    && apt-get install tesseract-ocr -y \
    && apt-get clean \
    && apt-get autoremove

# Best Model
COPY bin/eng.traineddata /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata

# Create Environment
COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml && conda clean -a -c -q && conda activate django-ocr-service

# System packages
RUN apt-get update && apt-get install -y curl

ARG DB_PASSWORD
ENV DB_PASSWORD=$DB_PASSWORD

ARG DB_HOST
ENV DB_HOST=$DB_HOST

ARG DB_NAME
ENV DB_NAME=$DB_NAME

ARG DB_USER
ENV DB_USER=$DB_USER

ARG SECRET_KEY
ENV SECRET_KEY=$SECRET_KEY

ARG AWS_ACCESS_KEY_ID
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID

ARG AWS_SECRET_ACCESS_KEY
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

ARG DJANGO_SUPERUSER_PASSWORD
ENV DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD

RUN mkdir -p /logs
RUN chmod 774 /logs

RUN mkdir -p /SRC/config
RUN chmod 774 /SRC
COPY django_ocr_service /SRC
ADD config/config_docker_local.yml /SRC/config/config.yml

WORKDIR /SRC/django_ocr_service

EXPOSE 8080

CMD bash startapp.sh
