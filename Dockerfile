FROM python:3.10.12-alpine

# Install system dependencies
RUN apk add --update --no-cache \
    libffi-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf \
    ttf-opensans \
    gobject-introspection

WORKDIR /django_point_of_sale

COPY . /django_point_of_sale

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

WORKDIR /django_point_of_sale/django_pos
