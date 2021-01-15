/* Compatibility */
if(!Date.now) {
	Date.now = function now() {
		return Date.getTime();
	};
}

class Vote {
	constructor(value) {
		this.value = value;
		
		this.upvoteClass = 'content-upvote';
		this.downvoteClass = 'content-downvote';
		this.activeClass = '-active';
	}
	
	attachToElements(upvoteElement,downvoteElement,counterText) {
		for(let arg of arguments) {
			if(arg === undefined || arg === null) {
				return;
			}
		}
		
		this.upvoteElement = upvoteElement; // Upvote button element
		this.downvoteElement = downvoteElement; // Downvote button element
		this.counterText = counterText; // Text for the vote counter
	}
	
	get activeUpvoteClass() {
		return this.upvoteClass+this.activeClass;
	}
	
	get activeDownvoteClass() {
		return this.downvoteClass+this.activeClass;
	}
	
	change(value) {
		var _temp = this.counterText.textContent.split('/');
		var nUpvotes = parseInt(_temp[0]);
		var nDownvotes = parseInt(_temp[1]);
		
		if(value === 1) {
			// change downvote to upvote
			if(this.upvoteElement.className === this.upvoteClass
			&& this.downvoteElement.className === this.activeDownvoteClass) {
				this.upvoteElement.className = this.activeUpvoteClass;
				this.downvoteElement.className = this.downvoteClass;
				nUpvotes++;
				nDownvotes--;
			}
			// remove upvote
			else if(this.upvoteElement.className === this.activeUpvoteClass) {
				this.upvoteElement.className = this.upvoteClass;
				nUpvotes--;
			}
			// just add a upvote
			else if(this.upvoteElement.className === this.upvoteClass) {
				this.upvoteElement.className = this.activeUpvoteClass;
				nUpvotes++;
			}
		} else if(value === -1) {
			// change upvote to downvote
			if(this.upvoteElement.className === this.activeUpvoteClass
			&& this.downvoteElement.className === this.downvoteClass) {
				this.upvoteElement.className = this.upvoteClass;
				this.downvoteElement.className = this.activeDownvoteClass;
				nDownvotes++;
				nUpvotes--;
			}
			// remove downvote
			else if(this.downvoteElement.className === this.activeDownvoteClass) {
				this.downvoteElement.className = this.downvoteClass;
				nDownvotes--;
			}
			// just add a downvote
			else if(this.downvoteElement.className === this.downvoteClass) {
				this.downvoteElement.className = this.activeDownvoteClass;
				nDownvotes++;
			}
		}
		this.counterText.textContent = `${nUpvotes}/${nDownvotes}`;
		console.log(`${nUpvotes}/${nDownvotes}`);
	}
}

function postVote(pid,value) {
	var xhr = new XMLHttpRequest();
	
	// Send a form POST request to the server for post votes
	xhr.open('POST',`/post/vote/${pid}`,true);
	
	// Method callback when request finishes
	xhr.onreadystatechange = function() {
		if(xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
			// Create new vote class
			vote = new Vote(value);
			
			// Attach corresponding elements
			vote.attachToElements(
				document.getElementById(`${pid}-post-upvote`),
				document.getElementById(`${pid}-post-downvote`),
				document.getElementById(`${pid}-post-counter`)
			);
			
			// Change text accordingly
			vote.change(value);
		}
	}
	
	// Send request
	xhr.send(`value=${value}`);
}

function commentVote(id,value) {
	var xhr = new XMLHttpRequest();
	
	// Send a form POST request to the server for comment votes
	xhr.open('POST',`/comment/vote/${id}`,true);
	
	// Method callback when request finishes
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			// Create new vote class
			vote = new Vote(value);
			
			// Attach corresponding elements
			vote.attachToElements(
				document.getElementById(`${id}-comment-upvote`),
				document.getElementById(`${id}-comment-downvote`),
				document.getElementById(`${id}-comment-counter`)
			);
			
			// Change text accordingly
			vote.change(id,value);
		}
	}
	
	// Send request
	xhr.send(`value=${value}`);
}

function follow(uid,e) {
	var xhr = new XMLHttpRequest();
	var url;
	var text;
	if(e.value === 'Unfollow') {
		url = `/user/unfollow/${uid}`;
		text = 'Follow';
	} else {
		url = `/user/follow/${uid}`;
		text = 'Unfollow';
	}
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			e.value = text;
		}
	}
	xhr.send();
}

function subscribe(bid,e) {
	var xhr = new XMLHttpRequest();
	var url;
	var text;
	if(e.value === 'Unsubscribe') {
		url = `/board/unsubscribe/${bid}`;
		text = 'Subscribe';
	} else {
		url = `/board/subscribe/${bid}`;
		text = 'Unsubscribe';
	}
	xhr.open('POST',url,true);
	xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			e.value = text;
		}
	}
	xhr.send();
}

function reply_comment(id) {
	var txt = document.getElementById(id);
	
	// Toggle on/off visibility
	if(txt.style.display == 'none') { txt.style.display = 'block'; }
	else { txt.style.display = 'none'; }
}

function handle_is_link(checkbox) {
	var txt = document.getElementById('link-text');
	
	if(txt.style.display == 'none') { txt.style.display = 'block'; }
	else { txt.style.display = 'none'; }
}

function update_content_time() {
	var list = document.getElementsByClassName('content-datetime');
	var time = Date.now();
	var ctime = Math.floor(time/1000);
	for(var e of list) {
		var otime = parseInt(e.getAttribute('value'));
		var diff = ctime-otime;
		
		// Convert diff to readable
		var text;
		
		if(diff <= 60) {
			text = diff+' seconds ago';
		} else if(diff >= 61 && diff <= 60*60) {
			text = Math.floor(diff/60)+' minutes and '+Math.floor(diff%60)+' seconds ago';
		} else if(diff >= (60*60)+1 && diff <= (60*60*24)) {
			text = Math.floor(diff/(60*60))+' hours and '+Math.floor((diff/60)%60)+' minutes ago';
		} else if(diff >= (60*60*24)+1) {
			text = Math.floor(diff/(60*60*24))+' days and '+Math.floor((diff/24)%24)+' hours ago';
		}
		
		e.innerText = text;
	}
}

var gpid;

// display full image when clicking on image block thing
function full_image(pid) {
	var e = document.getElementById('image-full-'+pid);
	var s = document.getElementById('smoke-curtain');
	
	e.classList.remove('fucking-die');
	s.classList.remove('fucking-die');
	
	e.style.display = 'block';
	s.style.display = 'block';
	
	e.animationName = 'fade-out';
	s.animationName = 'fade-in';
	
	gpid = pid;
}

// close image when clicking outside it
window.addEventListener('click', function(m) {
	var e = document.getElementById('image-full-'+gpid);
	var d = document.getElementById('image-full-dispenser-'+gpid);
	var s = document.getElementById('smoke-curtain');
	
	if(e === null || s === null || d === null) {
		return;
	}
	
	if(!e.contains(m.target) && !d.contains(m.target)) {
		e.classList.add('fucking-die');
		s.classList.add('fucking-die');
	}
});

window.addEventListener('animationend', function(m) {
	var e = document.getElementById('image-full-'+gpid);
	var s = document.getElementById('smoke-curtain');
	
	if(e === null || s === null) {
		return;
	}
	
	if(e.classList.contains('fucking-die') && s.classList.contains('fucking-die')) {
		e.style.display = 'none';
		s.style.display = 'none';
	}
});
