# schron/cli.py

import click
from .api_client import APIClient

# Инициализация API клиента
api_client = APIClient()

@click.group()
def cli():
    """Schron CLI Utility"""
    pass

@cli.command()
def register():
    """Зарегистрировать нового пользователя"""
    name = click.prompt("Введите ваше имя")
    email = click.prompt("Введите ваш email")
    password = click.prompt("Введите ваш пароль", hide_input=True, confirmation_prompt=True)
    api_client.register(name, email, password)

@cli.command()
def login():
    """Войти в систему"""
    email = click.prompt("Введите ваш email")
    password = click.prompt("Введите ваш пароль", hide_input=True)
    api_client.login(email, password)

@cli.command()
@click.argument('namespace_name')
def create_namespace(namespace_name):
    """Создать новый неймспейс"""
    api_client.create_namespace(namespace_name)

@cli.command()
@click.argument('group_name')
@click.option('--namespace', default="default", help='Имя неймспейса')
def create_group(group_name, namespace):
    """Создать новую группу"""
    api_client.create_group(group_name, namespace_name=namespace)

@cli.command()
@click.argument('application_name')
@click.option('--group', default="root", help='Имя группы')
def create_application(application_name, group):
    """Создать новое приложение"""
    api_client.create_application(application_name, group_name=group)

@cli.command()
@click.argument('secret_input')
def save(secret_input):
    """Сохранить секрет в формате: group_name/app_name/key=value"""
    try:
        # Разбор входных данных
        group_name, app_name, key_value = secret_input.split('/', 2)
        key, value = key_value.split('=', 1)
    except ValueError:
        click.echo("Неверный формат ввода. Используйте: group_name/app_name/key=value")
        return

    api_client.save_secret(group_name, app_name, key, value)

@cli.command()
@click.argument('secret_input')
def get(secret_input):
    """Получить секрет в формате: group_name/app_name/key"""
    try:
        group_name, app_name, key = secret_input.split('/', 2)
    except ValueError:
        click.echo("Неверный формат ввода. Используйте: group_name/app_name/key")
        return

    api_client.get_secret(group_name, app_name, key)

@cli.command()
@click.argument('secret_input')
def delete(secret_input):
    """Удалить секрет в формате: group_name/app_name/key"""
    try:
        group_name, app_name, key = secret_input.split('/', 2)
    except ValueError:
        click.echo("Неверный формат ввода. Используйте: group_name/app_name/key")
        return

    api_client.delete_secret(group_name, app_name, key)

def main():
    cli()

if __name__ == "__main__":
    cli()
