# Xaiecon
Censorship resistant platform, decentralized and federated.

## Install
### Manual
To install just clone the repository and then install the proper dependencies via:
`sudo apt install postgresql python3 python3-pip`

Install the python dependencias via this command:
`pip3 install -r requirements.txt`

Allow local connections on postgresql, this requires accesing `/etc/postgresql/(version)/main/pg_hba.conf`
Exchange `ident` and `peer` for `trust`. This will allow all local users to connect to PostgreSQL, so be cautious.

After that create a user for RW access to the database, otherwise use postgres user if you are lazy (don't do this on a production enviroment).
`sudo -u postgres psql`

Create the database, normally it can be any name but i recommend calling it `xaiecon`.
`CREATE DATABASE xaiecon;`

Exit postgresql with `\\q`. Then execute the following, to apply the `schema.sql` into the xaiecon database.
`sudo -u postgres psql -d xaiecon < schema.sql`

Then run the server with one single command:
`sh run.sh`

Visit `localhost:5000` on your browser to see your instance running.

### Docker
Clone the repository via `git clone https://gitlab.com/superleaf1995/xaiecon`.

Then build the docker image with the following command: `sudo docker build -t xaiecon:1.0 .`

This process can take a while, go grab yourself a coffe in the meanwhile.

After that, just run `sudo docker run -p 5000:8000 --name xai xaiecon:1.0` to run the server, then visit `localhost:5000` for seeing your new Xaiecon node.

The Dockerfile will make a user called `xaiuser` with password `xaipass` on the container. This user is made with sufficient privileges on the database. However it lacks UNIX privileges, made mostly to not wreck havoc inside the container :)