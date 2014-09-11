drop table if exists user;
create table user (
	user_id integer primary key,
	username text unique not null,
	password text,
	admin boolean not null default 0,
	directory text not null);

drop table if exists job;
create table job (
	job_id integer primary key,
	user_id not null references user(user_id),
	status text not null default 'waiting',
	script blob not null,
	start_time timestamp,
	end_time timestamp,
	out text,
	err text);

drop table if exists clipboard;
create table clipboard (
    user_id integer not null references user(user_id),
    file text not null);
