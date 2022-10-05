# hw05_final - спринт №6 в Яндекс.Практикум

## Спринт 6 - Проект спринта: подписки на авторов

### Добавлена возможность:
- осуществлять подписки/отписки на авторов постов.

### Использованный стек технологий:
- Django==2.2.16
- mixer==7.1.2
- Pillow==8.3.1
- pytest==6.2.4
- pytest-django==4.4.0
- pytest-pythonpath==0.7.3
- requests==2.26.0
- six==1.16.0
- sorl-thumbnail==12.7.0
- Faker==12.0.1

### Настройка и запуск на компьютере
Клонируем проект:
```
https://github.com/32Aleksey32/hw05_final.git
```
Переходим в папку с проектом:
```
cd hw05_final
```
Устанавливаем виртуальное окружение:
```
python -m venv venv
```
Активируем виртуальное окружение:
```
source venv/Scripts/activate
```
Устанавливаем зависимости:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Применяем миграции:
```
python yatube/manage.py makemigrations
python yatube/manage.py migrate
```
Создаем супер пользователя:
```
python yatube/manage.py createsuperuser
```
Запускаем проект:
```
python yatube/manage.py runserver
```
После чего проект будет доступен по адресу http://127.0.0.1:8000/

Заходим в http://127.0.0.1:8000/admin и создаем группы и записи. После чего записи и группы появятся на главной странице.
