DROP TABLE IF EXISTS xaiecon_statics;
DROP TABLE IF EXISTS xaiecon_logs;
DROP TABLE IF EXISTS xaiecon_serverchains;

DROP TABLE IF EXISTS xaiecon_votes;
DROP TABLE IF EXISTS xaiecon_flags;

DROP TABLE IF EXISTS xaiecon_comments;
DROP TABLE IF EXISTS xaiecon_posts;
DROP TABLE IF EXISTS xaiecon_boards;

DROP TABLE IF EXISTS xaiecon_api_app;
DROP TABLE IF EXISTS xaiecon_board_ban_rel;
DROP TABLE IF EXISTS xaiecon_users;
DROP TABLE IF EXISTS xaiecon_categories;

CREATE TABLE xaiecon_users(
	id SERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	username VARCHAR(255) NOT NULL,
	creation_date TIMESTAMP DEFAULT NOW(),
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
	ban_reason VARCHAR(255)
);

CREATE TABLE xaiecon_categories(
	id SERIAL PRIMARY KEY,
	creation_date TIMESTAMP DEFAULT NOW(),
	name VARCHAR(255)
);

CREATE TABLE xaiecon_boards(
	id SERIAL PRIMARY KEY,
	creation_date TIMESTAMP DEFAULT NOW(),
	name VARCHAR(255),
	descr VARCHAR(4095),
	keywords VARCHAR(255),
	image_file VARCHAR(255),
	category_id INT REFERENCES xaiecon_categories(id),
	user_id INT REFERENCES xaiecon_users(id)
);

CREATE TABLE xaiecon_posts(
	id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	views INT DEFAULT 1,
	body VARCHAR(16000),
	link_url VARCHAR(4095),
	is_link BOOLEAN DEFAULT FALSE,
	is_nsfw BOOLEAN DEFAULT FALSE,
	is_deleted BOOLEAN DEFAULT FALSE,
	creation_date TIMESTAMP DEFAULT NOW(),
	keywords VARCHAR(255),
	number_comments INT DEFAULT 0,
	downvote_count INT DEFAULT 0,
	upvote_count INT DEFAULT 0,
	total_vote_count INT DEFAULT 0,
	category_id INT REFERENCES xaiecon_categories(id),
	user_id INT REFERENCES xaiecon_users(id),
	board_id INT REFERENCES xaiecon_boards(id)
);

CREATE TABLE xaiecon_flags(
	id SERIAL PRIMARY KEY,
	creation_date TIMESTAMP DEFAULT NOW(),
	reason VARCHAR(4095),
	post_id INT REFERENCES xaiecon_posts(id),
	user_id INT REFERENCES xaiecon_users(id)
);

CREATE TABLE xaiecon_comments(
	id SERIAL PRIMARY KEY,
	creation_date TIMESTAMP DEFAULT NOW(),
	body VARCHAR(4095),
	downvote_count INT DEFAULT 0,
	upvote_count INT DEFAULT 0,
	total_vote_count INT DEFAULT 0,
	post_id INT REFERENCES xaiecon_posts(id),
	user_id INT REFERENCES xaiecon_users(id),
	comment_id INT REFERENCES xaiecon_comments(id)
);

CREATE TABLE xaiecon_votes(
	id SERIAL PRIMARY KEY,
	creation_date TIMESTAMP DEFAULT NOW(),
	comment_id INT REFERENCES xaiecon_comments(id),
	post_id INT REFERENCES xaiecon_posts(id),
	user_id INT REFERENCES xaiecon_users(id),
	value BIGINT DEFAULT 1
);

CREATE TABLE xaiecon_logs(
	id SERIAL PRIMARY KEY,
	creation_date TIMESTAMP DEFAULT NOW(),
	name VARCHAR(255) NOT NULL
);

CREATE TABLE xaiecon_serverchains(
	id SERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	ip_addr VARCHAR(4095) NOT NULL,
	is_banned BOOLEAN DEFAULT FALSE,
	is_active BOOLEAN DEFAULT FALSE,
	is_online BOOLEAN DEFAULT FALSE,
	is_share_posts BOOLEAN DEFAULT FALSE,
	is_share_boards BOOLEAN DEFAULT FALSE,
	is_share_users BOOLEAN DEFAULT FALSE,
	is_allow_cross_vote BOOLEAN DEFAULT FALSE
);

CREATE TABLE xaiecon_board_ban_rel(
	id SERIAL PRIMARY KEY,
	expiration_date TIMESTAMP DEFAULT NOW(),
	reason VARCHAR(255) NOT NULL,
	user_id INT REFERENCES xaiecon_users(id)
);

CREATE TABLE xaiecon_api_app(
	id SERIAL PRIMARY KEY,
	name VARCHAR(128),
	token VARCHAR(128),
	creation_date TIMESTAMP DEFAULT NOW(),
	user_id INT REFERENCES xaiecon_users(id)
);

INSERT INTO xaiecon_categories(name) VALUES
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
	('Other');

INSERT INTO xaiecon_users(name,username,biography,password,auth_token) VALUES('guest','guest','This is the default guest user','uncreatable','uncreatable')
