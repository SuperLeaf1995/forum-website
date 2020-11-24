DROP TABLE IF EXISTS xaiecon_oauthclient;
DROP TABLE IF EXISTS xaiecon_oauthapp;
DROP TABLE IF EXISTS xaiecon_flag;
DROP TABLE IF EXISTS xaiecon_notification;
DROP TABLE IF EXISTS xaiecon_log;
DROP TABLE IF EXISTS xaiecon_board_sub;
DROP TABLE IF EXISTS xaiecon_board_ban;
DROP TABLE IF EXISTS xaiecon_apiapp;
DROP TABLE IF EXISTS xaiecon_serverchain;
DROP TABLE IF EXISTS xaiecon_vote;
DROP TABLE IF EXISTS xaiecon_view;
DROP TABLE IF EXISTS xaiecon_comment;
DROP TABLE IF EXISTS xaiecon_post;
DROP TABLE IF EXISTS xaiecon_board;
DROP TABLE IF EXISTS xaiecon_category;
DROP TABLE IF EXISTS xaiecon_user;

CREATE TABLE xaiecon_user(
	id SERIAL PRIMARY KEY,
	name VARCHAR(255),
	username VARCHAR(255) NOT NULL,
	biography VARCHAR(8000),
	password VARCHAR(510) NOT NULL,
	auth_token VARCHAR(510) NOT NULL,
	image_file VARCHAR(255),
	email VARCHAR(255),
	is_show_email BOOLEAN DEFAULT FALSE,
	phone VARCHAR(255),
	is_show_phone BOOLEAN DEFAULT FALSE,
	fax VARCHAR(255),
	is_show_fax BOOLEAN DEFAULT FALSE,
	is_nsfw BOOLEAN DEFAULT FALSE,
	is_admin BOOLEAN DEFAULT FALSE,
	is_banned BOOLEAN DEFAULT FALSE,
	can_make_board BOOLEAN DEFAULT FALSE,
	ban_reason VARCHAR(255),
	creation_date INT,
	net_points INT,
	fallback_thumb VARCHAR(64) NOT NULL
);

CREATE TABLE xaiecon_category(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	name VARCHAR(255)
);

CREATE TABLE xaiecon_board(
	id SERIAL PRIMARY KEY,
	name VARCHAR(255),
	descr VARCHAR(4095),
	keywords VARCHAR(255),
	is_banned BOOLEAN DEFAULT FALSE,
	ban_reason VARCHAR(255),
	has_icon BOOLEAN DEFAULT FALSE,
	icon_file VARCHAR(255),
	creation_date INT,
	sub_count INT,
	fallback_thumb VARCHAR(64) NOT NULL,
	category_id INT REFERENCES xaiecon_category(id) ON UPDATE CASCADE,
	user_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE
);

CREATE TABLE xaiecon_post(
	id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	views INT DEFAULT 1,
	body VARCHAR(16000) NOT NULL,
	link_url VARCHAR(4095),
	is_link BOOLEAN DEFAULT FALSE,
	is_nsfw BOOLEAN DEFAULT FALSE,
	is_deleted BOOLEAN DEFAULT FALSE,
	creation_date INT,
	keywords VARCHAR(255),
	number_comments INT DEFAULT 0,
	downvote_count INT DEFAULT 0,
	upvote_count INT DEFAULT 0,
	total_vote_count INT DEFAULT 0,
	body_html VARCHAR(16000) NOT NULL,
	embed_html VARCHAR(16000),
	is_image BOOLEAN DEFAULT FALSE,
	is_thumb BOOLEAN DEFAULT FALSE,
	image_file VARCHAR(255),
	thumb_file VARCHAR(255),
	is_nuked BOOLEAN DEFAULT FALSE,
	show_votes BOOLEAN DEFAULT TRUE,
	nuker_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE,
	category_id INT REFERENCES xaiecon_category(id) ON UPDATE CASCADE,
	user_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE,
	board_id INT REFERENCES xaiecon_board(id) ON UPDATE CASCADE
);

CREATE TABLE xaiecon_flag(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	reason VARCHAR(16000),
	post_id INT REFERENCES xaiecon_post(id) ON UPDATE CASCADE,
	user_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE
);

CREATE TABLE xaiecon_comment(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	body VARCHAR(16000),
	body_html VARCHAR(16000),
	downvote_count INT DEFAULT 0,
	upvote_count INT DEFAULT 0,
	total_vote_count INT DEFAULT 0,
	post_id INT REFERENCES xaiecon_post(id) ON UPDATE CASCADE,
	user_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE,
	comment_id INT REFERENCES xaiecon_comment(id) ON UPDATE CASCADE
);

CREATE TABLE xaiecon_vote(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	comment_id INT REFERENCES xaiecon_comment(id) ON UPDATE CASCADE,
	post_id INT REFERENCES xaiecon_post(id) ON UPDATE CASCADE,
	user_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE,
	value BIGINT DEFAULT 1
);

CREATE TABLE xaiecon_view(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	post_id INT REFERENCES xaiecon_post(id) ON UPDATE CASCADE,
	user_id INT REFERENCES xaiecon_user(id) ON UPDATE CASCADE
);

CREATE TABLE xaiecon_log(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	name VARCHAR(255) NOT NULL
);

CREATE TABLE xaiecon_serverchain(
	id SERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	ip_addr VARCHAR(255) NOT NULL,
	endpoint_url VARCHAR(255) NOT NULL,
	internal_token VARCHAR(255) NOT NULL,
	external_token VARCHAR(255) NOT NULL,
	is_banned BOOLEAN DEFAULT FALSE,
	is_active BOOLEAN DEFAULT FALSE,
	is_online BOOLEAN DEFAULT FALSE,
	creation_date INT
);

CREATE TABLE xaiecon_board_ban(
	id SERIAL PRIMARY KEY,
	expiration_date INT,
	creation_date INT,
	reason VARCHAR(255) NOT NULL,
	board_id INT REFERENCES xaiecon_board(id),
	user_id INT REFERENCES xaiecon_user(id)
);

CREATE TABLE xaiecon_board_sub(
	id SERIAL PRIMARY KEY,
	creation_date INT,
	board_id INT REFERENCES xaiecon_board(id),
	user_id INT REFERENCES xaiecon_user(id)
);

-- API App
CREATE TABLE xaiecon_apiapp(
	id SERIAL PRIMARY KEY,
	name VARCHAR(128),
	token VARCHAR(128),
	creation_date INT,
	user_id INT REFERENCES xaiecon_user(id)
);

-- OAuth App
CREATE TABLE xaiecon_oauthapp(
	id SERIAL PRIMARY KEY,
	client_id VARCHAR(128) NOT NULL,
	client_secret VARCHAR(128) NOT NULL,
	name VARCHAR(128) NOT NULL,
	redirect_uri VARCHAR(128) NOT NULL,
	creation_date INT,
	user_id INT REFERENCES xaiecon_user(id)
);

CREATE TABLE xaiecon_oauthclient(
	id SERIAL PRIMARY KEY,
	oauth_code VARCHAR(128) NOT NULL,
	access_token VARCHAR(128) NOT NULL,
	refresh_token VARCHAR(128) NOT NULL,
	scope_read BOOLEAN DEFAULT FALSE,
	scope_vote BOOLEAN DEFAULT FALSE,
	scope_comment BOOLEAN DEFAULT FALSE,
	scope_nuke BOOLEAN DEFAULT FALSE,
	scope_yank BOOLEAN DEFAULT FALSE,
	scope_kick BOOLEAN DEFAULT FALSE,
	scope_post BOOLEAN DEFAULT FALSE,
	scope_update BOOLEAN DEFAULT FALSE,
	scope_board BOOLEAN DEFAULT FALSE,
	scope_write BOOLEAN DEFAULT FALSE,
	oauthapp_id INT REFERENCES xaiecon_oauthapp(id),
	user_id INT REFERENCES xaiecon_user(id)
);

CREATE TABLE xaiecon_notification(
	id SERIAL PRIMARY KEY,
	is_read BOOLEAN DEFAULT FALSE,
	body VARCHAR(16000) NOT NULL,
	body_html VARCHAR(16000) NOT NULL,
	creation_date INT,
	user_id INT REFERENCES xaiecon_user(id)
);

INSERT INTO xaiecon_category(name) VALUES
	('Culture'),
	('Politics'),
	('News'),
	('Humor'),
	('Animals'),
	('Fiction'),
	('Programming'),
	('Anarchy'),
	('Pictures'),
	('Technology'),
	('Nsfw'),
	('Mathematics'),
	('Nonsense'),
	('Videogames'),
	('Other'),
	('Sports');

INSERT INTO xaiecon_user(name,username,biography,password,auth_token,fallback_thumb) VALUES('guest','guest','This is the default guest user','uncreatable','uncreatable','golden.png')
