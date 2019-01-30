FROM python:3.5

ENTRYPOINT ["./docker-entrypoint.sh"]
EXPOSE 5000

# Working directory
RUN mkdir -p /app
WORKDIR /app

# Apache Airflow
ENV AIRFLOW_GPL_UNIDECODE yes

# Install the Python requirements
ADD requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the source files
COPY . /app
