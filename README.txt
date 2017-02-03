OpenProcurement is initiative to develop software powering tenders database and reverse auction.

The Open Procurement Open EU procedure is plugin to Open Procurement API software.

This documentation is available at http://openeu.api-docs.openprocurement.org/en/latest/index.html

Full documentation about OpenProcurement API is accessible at http://api-docs.openprocurement.org/


КОРОТКА ІНСТРУКЦІЯ ДЛЯ ГЕНЕРУВАННЯ ДОКУМЕНТАЦІЇ

Запуск couchdb

1) Для того, щоб запустити couchdb слід створити конфігураційний файл couchdb.ini. Приклад конфігураційного файлу приведено нижче:

[couchdb]
database_dir = /data/<user_name>/COUCHDB/couchdb
view_index_dir = /data/<user_name>/COUCHDB/couchdb
uri_file = /data/<user_name>/COUCHDB/couch.uri
username =
uuid = aeac27aa8f2da38bbad460ec161cd127

[log]
file = /data/<user_name>/COUCHDB/couch.log

[query_servers]
python = /data/<user_name>/COUCHDB/bin/couchpy

[httpd]
port = 5984
bind_address = 127.0.0.1

[compactions]
_default = [{db_fragmentation, "70%"}, {view_fragmentation, "60%"}, {from, "00:00"}, {to, "04:00"}, {strict_window, true}]

[compaction_daemon]
check_interval = 300

[couch_httpd_oauth]
use_users_db = true

[couchdb]
delayed_commits = false

[admins]
op = -pbkdf2-f4ebfcb6646dea16856e8cf51ba366e389abfff5,35d43151d88da925336499252c9d265e,10

[couch_httpd_auth]
secret = 1e04a175c0c6a963d38ae593ef9ac55b


Де замість <user_name> можна вставити свій user name.

2) запустити сесію couchdb:

> couchdb -a <path_to_folder_containing_couchdb.ini>/couchdb.ini

Маючи запущену сесію із couchdb можна перейти до генерування скриптів із реквестами і респонсами



Генерування скриптів із реквестами і респонсами із юніттестів

1) З метою уникнення конфлікту версій пакетів слід розбудовувати buildout із середовища із мінімальним (дефолтним) набором python-пакетів
Для цього необхідно встановити максимально порожнє віртуальне оточення і проводити розбудову з нього
> virtualenv env --no-site-packages --no-setuptools
> . env/bin/activate

2) Для роботи із документацією слід розбудовувати buildout із конфігураційним файлом docs.cfg
> python bootstrap.py -c docs.cfg
> bin/buildout -c docs.cfg

3) У віртуальному оточенні тепер нема необхідності і його можна видалити
> deactivate
> rm -rf env

4) при додаванні нових тестів чи зміні старих слід "згенерувати" скрипти із реквестами і респонсами, що проходять у тест-кейсах
> bin/nosetests docs.py
ці скрипти потім додадуться у документацію

Наступним кроком є генерування власне документації.



Генерування документації зі скриптами із реквестами і респонсами

1) додати текст англійською в rst

2) згенерувати тексти для перекладу
> cd docs/_build; make gettext
> bin/sphinx-intl update -c docs/source/conf.py -p docs/_build/locale -l uk

3) перекласти .po файли

4) згенерувати .mo файли
> bin/sphinx-intl build -c docs/source/conf.py

5) перевірити в браузері
> cd docs/_build; make -e SPHINXOPTS="-D language='uk'" html

6)  видалити нумерацію рядків
sed -i -c "/#:.*/ d" docs/source/locale/uk/LC_MESSAGES/*.po
sed -i -c "/#:.*/ d" docs/source/locale/uk/LC_MESSAGES/standard/*.po

Документацію згенеровано.
