# vault-moretech
Here is solution for Vault More.tech

## Руководство по разворачиванию решения.

Для того, чтобы решение можно было протестировать, необходимо загрузить файлы репозитория на любой хост с установленным docker, docker composeб python 3.12. 
Далее необходимо создать файл .env и заполнить его. Необходимые значения:

База данных для аутентификации и работы с API:
```
MONGO_AUTH_INITDB_USERNAME
MONGO_AUTH_INITDB_PASSWORD
MONGO_AUTH_DB_NAME
MONGO_AUTH_DB_PORT
```

Для работы JWT:
```
JWT_SECRET
JWT_ALGORITHM
```

Для аутентификации по LDAP:
```
LDAP_SERVER
LDAP_BIND_DN
LDAP_BIND_PASSWORD
LDAP_SEARCH_BASE
```

База данных для хранения секретов:
```
SECRET_DB_TYPE=mongodb (в решении реализован и протестирован данный тип)
SECRET_DB_USERNAME
SECRET_DB_PASSWORD
SECRET_DB_NAME
SECRET_DB_PORT
```

Third-party storage ля мастер ключа (в прототипе реализовано хранение в .env):
```
TYPE_ENCRYPT
MASTER_KEY
```

После заполнения .env необходимо прописать команду `sudo docker compose up --build`.
В лог будут выводиться данные о работе веб-сервера и базы данных.

Есть два варианта использования решения:
- API 
- CLI (позволяет удобно использовать API)

#### API

Эксплуатация решения происходит следующим образом:
POST /auth/register 
POST /auth/login
Полученный Bearer токен необходимо передавать в заголовке Authorization

Подробности формата запроса/ответа можно узнать по эндпоинту /docs
При авторизованном доступе нужно обратиться к следующим локациям:
```
POST /api/namespaces — создать namespace
POST /api/groups — создать группу в namespace
POST /api/applications — создать приложение для хранения секретов
POST /applications/{application_id}/secrets — добавить секрет
GET /applications/{application_id}/secrets/{key} — получить секрет по ключу
DELETE /applications/{application_id}/secrets/{key} — удалить секрет по ключу
```

#### CLI

CLI позволяет удобно работать с API. 
Для работы с ним необходимо перейти в папку ./schron и прописать команду `pip install .`
Далее у вас в PATH появится библиотека schron.

```
schron --help — вывести все доступные команды
schron register — зарегистрироваться, login произойдет автоматически
schron login — авторизоваться
```
При регистрации создается неймспейс по умолчанию с именем вида default_<>
В неймспейсе создаётся группа root.

```
schron create-namespace <имя неймспейса> — создать namespace
schron create-group <имя группы> — создать группу
schron create-application <имя приложения>
```
Работа с секретами:
```
schron save <group>/<app>/<key>=<value> — сохранить секрет
schron get <group>/<app>/<key> — получить секрет
schron delete <group>/<app>/<key> — удалить секрет
```

*Примечание: может потребоваться дополнительная отладка*