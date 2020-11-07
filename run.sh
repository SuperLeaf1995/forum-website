# Flask config
export FLASK_APP=xaiecon
export FLASK_ENV=development
export SERVER_CONFIG_FILE=flask_config.cfg

# UTF8 stuff
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Other envars
export SQLALCHEMY_URL=postgresql://xaiuser:xaipass@localhost/xaiecon
export HCAPTCHA_SITE_KEY='sitekey'
export HCAPTCHA_SECRET_KEY='secretkey'

flask run --host=0.0.0.0