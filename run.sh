export FLASK_APP=xaiecon
export FLASK_ENV=development
export SQLALCHEMY_URL=postgresql://xaiuser:xaipass@localhost/xaiecon
export DOMAIN_NAME=localhost:5000

flask run --host=0.0.0.0
