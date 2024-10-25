# schron/api_client.py

import os
import json
import requests
import click
from threading import Lock
import string
import random

class MappingCache:
    """
    Класс для управления кэшированием сопоставлений имени и ID неймспейсов, групп и приложений.
    Кэш сохраняется в отдельных JSON-файлах в домашней директории пользователя.
    """
    def __init__(self, namespace_cache_file=None, group_cache_file=None, application_cache_file=None):
        self.namespace_cache_file = namespace_cache_file or os.path.expanduser("~/.schron_namespaces.json")
        self.group_cache_file = group_cache_file or os.path.expanduser("~/.schron_groups.json")
        self.application_cache_file = application_cache_file or os.path.expanduser("~/.schron_applications.json")
        self.lock = Lock()
        self.namespaces = {}
        self.groups = {}
        self.applications = {}
        self.load_cache()
    
    def load_cache(self):
        # Загрузка кэша неймспейсов
        self.namespaces = self._load_single_cache(self.namespace_cache_file, "неймспейсов")
        # Загрузка кэша групп
        self.groups = self._load_single_cache(self.group_cache_file, "групп")
        # Загрузка кэша приложений
        self.applications = self._load_single_cache(self.application_cache_file, "приложений")
    
    def _load_single_cache(self, file_path, cache_type):
        cache = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                cache = {}
        return cache
    
    def save_cache(self):
        with self.lock:
            # Сохранение кэша неймспейсов
            self._save_single_cache(self.namespace_cache_file, self.namespaces)
            # Сохранение кэша групп
            self._save_single_cache(self.group_cache_file, self.groups)
            # Сохранение кэша приложений
            self._save_single_cache(self.application_cache_file, self.applications)
    
    def _save_single_cache(self, file_path, cache_data):
        try:
            with open(file_path, 'w') as f:
                json.dump(cache_data, f, indent=4)
        except IOError:
            pass  # Можно добавить уведомление пользователю при необходимости
    
    # Методы для неймспейсов
    def get_namespace_id(self, name):
        return self.namespaces.get(name)
    
    def set_namespace_id(self, name, id_):
        self.namespaces[name] = id_
        self.save_cache()
    
    def remove_namespace(self, name):
        if name in self.namespaces:
            del self.namespaces[name]
            self.save_cache()
    
    # Методы для групп
    def get_group_id(self, name):
        return self.groups.get(name)
    
    def set_group_id(self, name, id_):
        self.groups[name] = id_
        self.save_cache()
    
    def remove_group(self, name):
        if name in self.groups:
            del self.groups[name]
            self.save_cache()
    
    # Методы для приложений
    def get_application_id(self, app_name):
        return self.applications.get(app_name)
    
    def set_application_id(self, app_name, app_id):
        self.applications[app_name] = app_id
        self.save_cache()
    
    def remove_application(self, app_name):
        if app_name in self.applications:
            del self.applications[app_name]
            self.save_cache()

class APIClient:
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Замените на ваш URL API
        self.token_file = os.path.expanduser("~/.schron_token")
        self.token = None
        self.cache = MappingCache()
        self.load_token()
    
    def save_token(self, token):
        with Lock():
            self.token = token
            try:
                with open(self.token_file, 'w') as f:
                    json.dump({"token": token}, f)
            except IOError:
                click.echo("Не удалось сохранить токен.")
    
    def load_token(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get("token")
            except (json.JSONDecodeError, IOError):
                click.echo("Не удалось загрузить токен.")
    
    def get_headers(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _handle_response(self, response, success_status):
        if response.status_code == success_status:
            return True
        elif response.status_code == 401:
            click.echo("Токен истёк или недействителен. Пожалуйста, выполните вход снова.")
            # Попытка повторного входа
            email = click.prompt("Введите ваш email")
            password = click.prompt("Введите ваш пароль", hide_input=True)
            if self.login(email, password):
                return True
            else:
                return False
        else:
            try:
                detail = response.json().get("detail", "Неизвестная ошибка.")
            except ValueError:
                detail = "Ответ сервера не является валидным JSON."
            click.echo(f"Ошибка: {detail}")
            return False
    
    def register(self, name, email, password):
        url = f"{self.base_url}/auth/register"
        data = {
            "name": name,
            "email": email,
            "password": password
        }
        try:
            response = requests.post(url, json=data, headers=self.get_headers(), proxies={})
            if response.status_code == 201:
                click.echo("Регистрация прошла успешно!")
                # Автоматический вход после регистрации
                self.login(email, password)
                # Создание дефолтного namespace и группы
                namespace_name = self.create_namespace(generate_default=True)
                if namespace_name:
                    self.create_group("root", namespace_name=namespace_name)
                return True
            else:
                try:
                    detail = response.json().get("detail", "Неизвестная ошибка.")
                except ValueError:
                    detail = "Ответ сервера не является валидным JSON."
                click.echo(f"Ошибка регистрации: {detail}")
                return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def login(self, email, password):
        url = f"{self.base_url}/auth/login"
        data = {
            "email": email,
            "password": password
        }
        try:
            response = requests.post(url, json=data, headers=self.get_headers(), proxies={})
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.save_token(token)
                click.echo("Вход выполнен успешно!")
                return True
            else:
                try:
                    detail = response.json().get("detail", "Неизвестная ошибка.")
                except ValueError:
                    detail = "Ответ сервера не является валидным JSON."
                click.echo(f"Ошибка входа: {detail}")
                return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def create_namespace(self, namespace_name=None, generate_default=False):
        if generate_default or not namespace_name:
            random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            namespace_name = f"default_{random_suffix}"
        
        url = f"{self.base_url}/api/namespaces"
        data = {"name": namespace_name}
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 201):
                click.echo(f"Неймспейс '{namespace_name}' успешно создан!")
                # Обновление кэша
                namespace_id = response.json().get("id")
                if namespace_id:
                    self.cache.set_namespace_id(namespace_name, namespace_id)
                return namespace_name
            return None
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return None
    
    def create_group(self, group_name, namespace_name):
        namespace_id = self.cache.get_namespace_id(namespace_name)
        if not namespace_id:
            click.echo(f"Неймспейс '{namespace_name}' не найден в кэше. Пожалуйста, создайте его сначала.")
            return False
        url = f"{self.base_url}/api/groups"
        data = {
            "name": group_name,
            "namespace_id": namespace_id
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 201):
                click.echo(f"Группа '{group_name}' успешно создана в неймспейсе '{namespace_name}'!")
                # Обновление кэша
                group_id = response.json().get("id")
                if group_id:
                    self.cache.set_group_id(group_name, group_id)
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def add_user_to_namespace(self, namespace_name, user_id, is_admin=False):
        namespace_id = self.cache.get_namespace_id(namespace_name)
        if not namespace_id:
            click.echo(f"Неймспейс '{namespace_name}' не найден в кэше.")
            return False
        url = f"{self.base_url}/api/namespaces/{namespace_id}/add_user"
        data = {
            "user_id": user_id,
            "is_admin": is_admin
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 200):
                role = "админ" if is_admin else "пользователь"
                click.echo(f"Пользователь с ID '{user_id}' добавлен в неймспейс '{namespace_name}' как {role}.")
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def remove_user_from_namespace(self, namespace_name, user_id):
        namespace_id = self.cache.get_namespace_id(namespace_name)
        if not namespace_id:
            click.echo(f"Неймспейс '{namespace_name}' не найден в кэше.")
            return False
        url = f"{self.base_url}/api/namespaces/{namespace_id}/remove_user"
        data = {
            "user_id": user_id
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 200):
                click.echo(f"Пользователь с ID '{user_id}' удалён из неймспейса '{namespace_name}'.")
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def add_user_to_group(self, group_name, user_email, role):
        group_id = self.cache.get_group_id(group_name)
        if not group_id:
            click.echo(f"Группа '{group_name}' не найдена в кэше.")
            return False
        url = f"{self.base_url}/api/groups/{group_id}/add_user"
        data = {
            "email": user_email,
            "role": role
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 200):
                click.echo(f"Пользователь с email '{user_email}' добавлен в группу '{group_name}' как '{role}'.")
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def remove_user_from_group(self, group_name, user_email):
        group_id = self.cache.get_group_id(group_name)
        if not group_id:
            click.echo(f"Группа '{group_name}' не найдена в кэше.")
            return False
        url = f"{self.base_url}/api/groups/{group_id}/remove_user"
        data = {
            "email": user_email
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 200):
                click.echo(f"Пользователь с email '{user_email}' удалён из группы '{group_name}'.")
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def create_application(self, app_name, group_name):
        group_id = self.cache.get_group_id(group_name)
        if not group_id:
            click.echo(f"Группа '{group_name}' не найдена в кэше.")
            return False
        url = f"{self.base_url}/api/applications"
        data = {
            "name": app_name,
            "group_id": group_id,
            "algorithm": "AES"  # Предполагая, что 'AES' является допустимым алгоритмом
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 201):
                click.echo(f"Приложение '{app_name}' успешно создано в группе '{group_name}'!")
                # Обновление кэша приложений
                app_id = response.json().get("id")
                if app_id:
                    self.cache.set_application_id(app_name, app_id)
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def save_secret(self, group_name, app_name, key, value):
        # Получение ID приложения из кэша
        app_id = self.cache.get_application_id(app_name)
        if not app_id:
            click.echo(f"Приложение '{app_name}' не найдено в кэше. Пожалуйста, создайте его сначала.")
            return False
        url = f"{self.base_url}/api/applications/{app_id}/secrets"
        data = {
            "secrets": {
                key: value
            }
        }
        headers = self.get_headers()
        try:
            response = requests.post(url, json=data, headers=headers, proxies={})
            if self._handle_response(response, 200):
                click.echo("Секрет успешно сохранен!")
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def get_secret(self, group_name, app_name, key):
        # Получение ID приложения из кэша
        app_id = self.cache.get_application_id(app_name)
        if not app_id:
            click.echo(f"Приложение '{app_name}' не найдено в кэше.")
            return None
        url = f"{self.base_url}/api/applications/{app_id}/secrets/{key}"
        headers = self.get_headers()
        try:
            response = requests.get(url, headers=headers, proxies={})
            if response.status_code == 200:
                try:
                    secret = response.json().get("secret")
                    if secret is not None:
                        click.echo(f"Секрет '{key}': {secret}")
                        return secret
                    else:
                        click.echo("Секрет не найден.")
                        return None
                except ValueError:
                    click.echo("Не удалось распарсить ответ от сервера.")
                    return None
            elif response.status_code == 404:
                click.echo("Секрет не найден.")
                return None
            else:
                self._handle_response(response, 200)
                return None
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return None
    
    def delete_secret(self, group_name, app_name, key):
        # Получение ID приложения из кэша
        app_id = self.cache.get_application_id(app_name)
        if not app_id:
            click.echo(f"Приложение '{app_name}' не найдено в кэше.")
            return False
        url = f"{self.base_url}/api/applications/{app_id}/secrets/{key}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers, proxies={})
            if self._handle_response(response, 200):
                click.echo("Секрет успешно удален!")
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def delete_namespace(self, namespace_name):
        namespace_id = self.cache.get_namespace_id(namespace_name)
        if not namespace_id:
            click.echo(f"Неймспейс '{namespace_name}' не найден в кэше.")
            return False
        url = f"{self.base_url}/api/namespaces/{namespace_id}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers, proxies={})
            if self._handle_response(response, 204):
                click.echo(f"Неймспейс '{namespace_name}' успешно удалён!")
                self.cache.remove_namespace(namespace_name)
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
    
    def delete_group(self, group_name):
        group_id = self.cache.get_group_id(group_name)
        if not group_id:
            click.echo(f"Группа '{group_name}' не найдена в кэше.")
            return False
        url = f"{self.base_url}/api/groups/{group_id}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers, proxies={})
            if self._handle_response(response, 204):
                click.echo(f"Группа '{group_name}' успешно удалена!")
                self.cache.remove_group(group_name)
                return True
            return False
        except requests.exceptions.RequestException as e:
            click.echo(f"Ошибка соединения: {e}")
            return False
