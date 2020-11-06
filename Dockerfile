FROM debian
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python3-pip python3 postgresql

# Install python3.7 requirements
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy the entire app into the working dir
COPY . /app

# Set enviroment variables
ENV FLASK_APP=xaiecon
ENV FLASK_ENV=development
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DOCKER=True
ENV SQLALCHEMY_DATABASE=postgresql://postgres:postgres@localhost/xecom

# Run flask
ENTRYPOINT [ "python3" ]
CMD [ "passenger_wsgi.py" ]
