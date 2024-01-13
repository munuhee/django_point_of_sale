FROM python:3.10.12-alpine

WORKDIR /django_point_of_sale

COPY . /django_point_of_sale

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

WORKDIR /django_point_of_sale/django_pos

EXPOSE 8000

CMD python manage.py runserver
