# Flask config
export FLASK_APP=xaiecon
export FLASK_ENV=development

# UTF8 stuff
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Other envars
export SQLALCHEMY_URL=postgresql://postgres:postgres@localhost/xaiecon
flask run -p 5000 -h 0.0.0.0
