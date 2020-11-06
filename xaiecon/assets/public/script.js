function status_change(id,value) {
	/* sucess voting */
	var c = document.getElementById(id+'-counter');
	var cnt = c.textContent.split('/');
	var u = document.getElementById(id+'-upvote');
	var d = document.getElementById(id+'-downvote');
	
	var downvotes = 0;
	var upvotes = 0;
	
	if(value == 1) {
		// change downvote to upvote
		if(u.className == 'content-upvote'
		&& d.className == 'content-downvote-active') {
			u.className = 'content-upvote-active';
			d.className = 'content-downvote';
			upvotes++;
		}
		// remove upvote
		else if(u.className == 'content-upvote-active') {
			u.className = 'content-upvote';
		}
		// just add a upvote
		else if(u.className == 'content-upvote') {
			u.className = 'content-upvote-active';
			upvotes++;
		}
	} else if(value == -1) {
		// change upvote to downvote
		if(u.className == 'content-upvote-active'
		&& d.className == 'content-downvote') {
			u.className = 'content-upvote';
			d.className = 'content-downvote-active';
			downvotes++;
		}
		// remove downvote
		else if(d.className == 'content-downvote-active') {
			d.className = 'content-downvote';
		}
		// just add a downvote
		else if(d.className == 'content-downvote') {
			d.className = 'content-downvote-active';
			downvotes++;
		}
	}
	
	str = upvotes+'/'+downvotes;
	c.textContent = str;
}

function vote_post(id,value) {
	var xhr = new XMLHttpRequest();
	var url = '/post/vote';
	var params = 'pid='+id+'&value='+value;
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			status_change(id,value);
		}
	}
	alert('Meme');
	xhr.send(params);
}

function vote_comment(id,value) {
	var xhr = new XMLHttpRequest();
	var url = '/comment/vote';
	var params = 'cid='+id+'&value='+value;
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			status_change(id,value);
		}
	}
	xhr.send(params);
}

