function status_change(uid,value) {
	/* sucess voting */
	var c = document.getElementById(uid+'-counter');
	var cnt = c.textContent.split('/');
	var u = document.getElementById(uid+'-upvote');
	var d = document.getElementById(uid+'-downvote');
	
	var downvotes = 0;
	var upvotes = 0;
	
	if(value == 1) {
		// change downvote to upvote
		if(u.className == 'post-upvote'
		&& d.className == 'post-downvote-active') {
			u.className = 'post-upvote-active';
			d.className = 'post-downvote';
			upvotes++;
		}
		// remove upvote
		else if(u.className == 'post-upvote-active') {
			u.className = 'post-upvote';
		}
		// just add a upvote
		else if(u.className == 'post-upvote') {
			u.className = 'post-upvote-active';
			upvotes++;
		}
	} else if(value == -1) {
		// change upvote to downvote
		if(u.className == 'post-upvote-active'
		&& d.className == 'post-downvote') {
			u.className = 'post-upvote';
			d.className = 'post-downvote-active';
			downvotes++;
		}
		// remove downvote
		else if(d.className == 'post-downvote-active') {
			d.className = 'post-downvote';
		}
		// just add a downvote
		else if(d.className == 'post-downvote') {
			d.className = 'post-downvote-active';
			downvotes++;
		}
	}
	
	str = upvotes+'/'+downvotes;
	c.textContent = str;
}

function vote(uid,value) {
	var xhr = new XMLHttpRequest();
	var url = '/post/vote';
	var params = 'pid='+uid+'&value='+value;
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			status_change(uid,value);
		}
	}
	xhr.send(params);
}

function vote(uid,value) {
	var xhr = new XMLHttpRequest();
	var url = '/comment/vote';
	var params = 'cid='+uid+'&value='+value;
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			status_change(uid,value);
		}
	}
	xhr.send(params);
}

