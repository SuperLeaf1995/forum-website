from xaiecon.classes.base import open_db
from xaiecon.classes.notification import Notification

def send_notification(msg: str, target_id: int):
	db = open_db()
	
	notification = Notification(
		body=msg,
		user_id=target_id)
	db.add(notification)
	db.commit()
	
	db.close()