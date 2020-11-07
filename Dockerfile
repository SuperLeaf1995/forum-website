FROM debian

# Install required dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y python3-pip python3 postgresql

# Copy the requirements
COPY ./requirements.txt /app/requirements.txt

# Install pip requirements
WORKDIR /app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Create user with sufficient privileges on database, but without privileges to cause havoc ;)
RUN useradd --create-home --shell /bin/bash xaiuser

# Setup PostgreSQL
USER postgres

# Allow local connections
RUN rm /etc/postgresql/11/main/pg_hba.conf && touch /etc/postgresql/11/main/pg_hba.conf
RUN echo 'local     all     all                 trust' >> /etc/postgresql/11/main/pg_hba.conf &&\
	echo 'host      all     all     0.0.0.0/0   trust' >> /etc/postgresql/11/main/pg_hba.conf

# PostgreSQL does not listen to 0.0.0.0, but it needs to do so in Docker.
# See relevant StackOverflow question: https://stackoverflow.com/questions/47890233/postgresql-docker-could-not-bind-ipv6-socket-cannot-assign-requested-address
RUN echo "listen_addresses='*'" >> /etc/postgresql/11/main/postgresql.conf

# Start PostgreSQL and assert that cluster is running
# Copy the schema into container
COPY ./schema.sql /app/schema.sql

RUN service postgresql start &&\
	psql --command "CREATE USER xaiuser WITH SUPERUSER PASSWORD 'xaipass'" &&\
	createdb -O xaiuser xaiecon &&\
	psql -d xaiecon < schema.sql

# Expose the PostgreSQL port
EXPOSE 5432

# Allow backups of databases and logs
VOLUME ['/etc/postgresql', '/var/log/postgresql', '/var/lib/postgresql']

# Change to root and do final steps
USER root

# Execute the server when the Docker container is run

# Copy entire app into container
COPY . /app

# Run the server with final sh script
RUN chmod 777 run.sh

USER xaiuser
CMD ./run.sh
