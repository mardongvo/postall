--справочник почтовых индексов
create table if not exists POSTINDEX(
postindex varchar(6) not null,
region varchar(60) not null,
autonom varchar(100) not null,
area varchar(100) not null,
city varchar(100) not null
);

create index p1 on POSTINDEX(postindex);

--справочник реестров отправки
create table if not exists REESTR(
id serial primary key,
ext_id integer default 0, --внешний id (сайта)
ext_date date not null, --внешняя дата отправки
rdate date not null,
locked integer default 0,
commentary varchar(100) default '' --примечание (ФИО)
);

-- почтовые отправления
create table if not exists MAILINFO(
id serial primary key,
ext_id integer default 0, --внешний id (сайта)
rid integer default 0, --reestr id
num varchar(14) not null default '',  -- номер почтового отправления
indexto varchar(6) default '', --
region varchar(60) default '', --
area varchar(100) default '',
city varchar(100)  default '', --
adresat varchar(255) default '', --
mass integer default 0, --вес в граммах
massp integer default 1, --количество листов письма (исп-ся для расчета веса)
location varchar(100) default '',
street varchar(100) default '',
house varchar(40) default '',
letter varchar(2) default '',
slash varchar(5) default '',
corpus varchar(5) default '',
building varchar(5) default '',
room varchar(20) default '',
commentary varchar(100) default '', --примечание
username varchar(60) default '',
lasterror varchar(100) default '', --ошибка выгрузки вовне
locked integer default 0 --заблокировано для изменений
);

create index p2 on mailinfo(rid);
create index p3 on mailinfo(num);

-- справочник адресов контрагентов
create table if not exists ADDRINFO(
sourcetype integer default 0, -- код источника адресов
regnum varchar(20), -- код контрагента из источника
indexto varchar(6) default '', --
region varchar(60) default '', --
area varchar(100) default '',
city varchar(100)  default '', --
adresat varchar(255) default '', --
location varchar(100) default '',
street varchar(100) default '',
house varchar(40) default '',
letter varchar(2) default '',
slash varchar(5) default '',
corpus varchar(5) default '',
building varchar(5) default '',
room varchar(20) default ''
);

create index p4 on addrinfo(regnum);

-- пользователи
create table if not exists FIO(
username varchar(60),
fio varchar(60),
UNIQUE (username)
);