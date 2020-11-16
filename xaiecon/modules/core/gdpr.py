#
# Module that asks user for permission to store cookies, redirects it
# to a "allow cookie" route and then returns to index.
#
# This is to comply to EU's GDPR
#

from flask import Blueprint, session

gdpr = Blueprint('gdpr',__name__,template_folder='templates')

@gdpr.route('/gdpr/agree', methods = ['GET'])
def agree_gdpr():
	session['agreed_gdpr'] = True
	return '',200

print('GDPR pages ... ok')
