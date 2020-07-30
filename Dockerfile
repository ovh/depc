FROM python:3.6

ENTRYPOINT ["./docker-entrypoint.sh"]
EXPOSE 5000

RUN apt-get update && apt-get install -y libsnappy-dev

# Working directory
RUN mkdir -p /app
WORKDIR /app

# Apache Airflow
ENV AIRFLOW_GPL_UNIDECODE yes

# Install the Python requirements
ADD requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install python-snappy==0.5.4
RUN pip install -r requirements.txt

# Copy the source files
COPY . /app
