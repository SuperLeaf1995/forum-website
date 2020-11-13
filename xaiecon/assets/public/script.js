function status_change(id,value) {
	/* sucess voting */
	var c = document.getElementById(id+'-counter');
	var cnt = c.textContent.split('/');
	var u = document.getElementById(id+'-upvote');
	var d = document.getElementById(id+'-downvote');
	
	var downvotes = 0;
	var upvotes = 0;

	upvotes = cnt[0];
	downvotes = cnt[1];
	
	if(value === 1) {
		// change downvote to upvote
		if(u.className === 'content-upvote'
		&& d.className === 'content-downvote-active') {
			u.className = 'content-upvote-active';
			d.className = 'content-downvote';
			upvotes++;
			downvotes--;
		}
		// remove upvote
		else if(u.className === 'content-upvote-active') {
			u.className = 'content-upvote';
			upvotes--;
		}
		// just add a upvote
		else if(u.className === 'content-upvote') {
			u.className = 'content-upvote-active';
			upvotes++;
		}
	} else if(value === -1) {
		// change upvote to downvote
		if(u.className === 'content-upvote-active'
		&& d.className === 'content-downvote') {
			u.className = 'content-upvote';
			d.className = 'content-downvote-active';
			downvotes++;
			upvotes--;
		}
		// remove downvote
		else if(d.className === 'content-downvote-active') {
			d.className = 'content-downvote';
			downvotes--;
		}
		// just add a downvote
		else if(d.className === 'content-downvote') {
			d.className = 'content-downvote-active';
			downvotes++;
		}
	}
	
	console.log(cnt);
	console.log(downvotes,upvotes);

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

function subscribe(bid,e) {
	var xhr = new XMLHttpRequest();
	var url;
	var text;
	var params = 'bid='+bid;
	if(e.value === 'Unsubscribe') {
		url = '/board/unsubscribe';
		text = 'Subscribe';
	} else {
		url = '/board/subscribe';
		text = 'Unsubscribe';
	}
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			e.value = text;
		}
	}
	xhr.send(params);
}

function reply_comment(idd) {
	var txt = document.getElementById(idd);
	if(txt.style.display == 'none') {
		txt.style.display = 'block';
	} else {
		txt.style.display = 'none';
	}
}

function handle_is_link(checkbox) {
	var txt = document.getElementById('link-text');
	if(checkbox.checked == true) {
		txt.style.display = 'block';
	} else {
		txt.style.display = 'none';
	}
}

function get_title_from_link(link_f) {
	var e = link_f
	var u = document.getElementById('link-text-input');

	// Get title by url
	var xhr = new XMLHttpRequest();

	xhr.open('GET','/post/title_by_url',true);
	xhr.setRequestHeader('Content-Type','application/x-www-form-urlencoded');

	// We dont give a fuck if the server is down, we need to get that title
	xhr.onreadystatechange = function() {
		if (xhr.readyState == 4) {
			e.value = xhr.responseText;
		}
	}
	xhr.send('url='+u.value);
}

var source = document.getElementById('link-text')
if(source !== null) {
	source.addEventListener('input',get_title_from_link);
}