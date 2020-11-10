function status_change(id,value){var c=document.getElementById(id+'-counter');var cnt=c.textContent.split('/');var u=document.getElementById(id+'-upvote');var d=document.getElementById(id+'-downvote');var downvotes=0;var upvotes=0;if(value==1){if(u.className=='content-upvote'&&d.className=='content-downvote-active'){u.className='content-upvote-active';d.className='content-downvote';upvotes++;}
else if(u.className=='content-upvote-active'){u.className='content-upvote';}
else if(u.className=='content-upvote'){u.className='content-upvote-active';upvotes++;}}else if(value==-1){if(u.className=='content-upvote-active'&&d.className=='content-downvote'){u.className='content-upvote';d.className='content-downvote-active';downvotes++;}
else if(d.className=='content-downvote-active'){d.className='content-downvote';}
else if(d.className=='content-downvote'){d.className='content-downvote-active';downvotes++;}}
str=upvotes+'/'+downvotes;c.textContent=str;}
function vote_post(id,value){var xhr=new XMLHttpRequest();var url='/post/vote';var params='pid='+id+'&value='+value;xhr.open('POST',url,true);xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');xhr.onreadystatechange=function(){if(xhr.readyState==4&&xhr.status==200){status_change(id,value);}}
xhr.send(params);}
function vote_comment(id,value){var xhr=new XMLHttpRequest();var url='/comment/vote';var params='cid='+id+'&value='+value;xhr.open('POST',url,true);xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');xhr.onreadystatechange=function(){if(xhr.readyState==4&&xhr.status==200){status_change(id,value);}}
xhr.send(params);}
function subscribe(bid,e){var xhr=new XMLHttpRequest();var url;var text;var params='bid='+bid;if(e.value==='Unsubscribe'){url='/board/unsubscribe';text='Subscribe';}else{url='/board/subscribe';text='Unsubscribe';}
xhr.open('POST',url,true);xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');xhr.onreadystatechange=function(){if(xhr.readyState==4&&xhr.status==200){e.value=text;}}
xhr.send(params);}
function reply_comment(idd){var txt=document.getElementById(idd);if(txt.style.display=='none'){txt.style.display='block';}else{txt.style.display='none';}}
function handle_is_link(checkbox){var txt=document.getElementById('link-text');if(checkbox.checked==true){txt.style.display='block';}else{txt.style.display='none';}}
function get_title_from_link(link_f){var e=link_f
var u=document.getElementById('link-text-input');var xhr=new XMLHttpRequest();xhr.open('GET','/post/title_by_url',true);xhr.setRequestHeader('Content-Type','application/x-www-form-urlencoded');xhr.onreadystatechange=function(){if(xhr.readyState==4){e.value=xhr.responseText;}}
xhr.send('url='+u.value);}
var source=document.getElementById('link-text')
if(source!==null){source.addEventListener('input',get_title_from_link);}