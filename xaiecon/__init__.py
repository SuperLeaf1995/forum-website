# Load function create_app from module xaiecon.factory
# This will load the factory function and make us happy
# About everything else :D
from xaiecon.factory import create_app

app = create_app()
if __name__ == '__main__':
	app.run()
