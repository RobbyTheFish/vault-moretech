![image](https://github.com/user-attachments/assets/02b5a147-f3cb-40a5-97cd-81f747da8daa)# Аналог Hashicorp Vault для хакатона MORE.Tech 2024
Данное решение было разработано в рамках работы над треком Vault на хакатоне more.tech (https://moretech.vtb.ru/vault).
Проект — менеджер секретов для удобного и безопасного хранения секретов, с которыми взаимодействуют сервисы.

## Контрибьюторы
Озеров Ярослав — github.com/RobbyTheFish (backend/devops)
Никита Селивёрстов — github.com/s1lver29 (backend/core)
Черкащенко Анастасия (PM/Design)

## Использованные технологии
- Python 3.12
- FastAPI
- Docker
- Motor

## Архитектура решения
![image](https://github.com/user-attachments/assets/39bd0b9d-8e7b-4273-9838-313d8c25a6b0)

## Пример работы
![image](https://github.com/user-attachments/assets/d04b17da-a43f-4305-ab09-5aa352095b48)


## Руководство по разворачиванию решения.

Для того, чтобы решение можно было протестировать, необходимо загрузить файлы репозитория на любой хост с установленным docker, docker compose, python 3.12. 
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
После чего у вас в PATH появится библиотека schron.

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

## Основной функционал проекта
1) Работа с секретами (добавление/удаление пар ключ:значение)
2) Создание групп пользователей и пространств имен для обеспечения изоляции и мультитенантности

Также реализована возможность интеграции с LDAP системой.

*Примечание: может потребоваться дополнительная отладка*

## Актуальность
Данный проект очень важен и актуален для компаний, которые зависят от внешних решений зарубежных интеграторов при хранении секретов, в частности Hashicorp Vault. 
Из-за юридических аспектов использование продуктов компании Hashicorp на территории РФ может быть сопряжено с некоторыми проблемами, также сам по себе интерфейс Hashicorp Vault является недостаточно удобным и не закрывает многие требования заказчика.
Мы постарались решить данную проблему.
### Векторы развития решения
Фичи, которые мы бы хотели реализовать:
- Ротация KeyRing
- Аудит доступа к секретам
- Seal/Auto Seal 
- Active-active кластеризация
- Реализация большего количества типов MFA
- Web UI

## License

MIT

---

