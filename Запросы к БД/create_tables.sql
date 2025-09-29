create table if not exists users (
	telegram_id integer primary key not null,
	username varchar(30)
);

create table if not exists user_words (
	word_id serial primary key,
	word_ru varchar(30) not null,
	word_en varchar(30) not null,
	user_id integer references users(telegram_id) not null
);

create table if not exists words (
	word_id serial primary key,
	word_ru varchar(30) not null,
	word_en varchar(30) not null
);
