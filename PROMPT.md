================================================================================
ПРОМПТ ДЛЯ НОВОГО ЧАТА - Cloud Lab Project (Финальная стабильная версия)
================================================================================

Ты - ИИ-ассистент, помогающий с проектом "Облако + мониторинг" на Arch Linux.

## АРХИТЕКТУРА ПРОЕКТА

Сервер: Arch Linux
Локальный IP: 192.168.1.102
Tailscale IP: 100.99.188.89
Пользователь: csn (пароль: lab123)
Пароль postgres: postgres

### УСТАНОВЛЕННЫЕ СЕРВИСЫ
- PostgreSQL 17 (порт 5432) - локально
- nginx (порт 80) - reverse proxy на Flask (работает)
- Prometheus (9090) + node_exporter (9100)
- Flask + psycopg2 + flask-login
- Tailscale (VPN)

### БАЗА ДАННЫХ
БД: cloud_lab
Пользователь: cloud_user (пароль: lab123)
Таблицы: files, metrics, users

### ПРИЛОЖЕНИЕ FLASK
Путь: /home/csn/cloud_app/
Порт: 8080
Сайт: http://100.99.188.89

### СТРУКТУРА ПРОЕКТА
/home/csn/cloud_app/
- app.py
- config.py
- models.py
- requirements.txt
- routes/
  - auth.py
  - cloud.py
  - monitor.py
  - diagnose.py
- utils/
  - db.py
  - helpers.py
- static/uploads/
- templates/
  - base.html
  - login.html
  - register.html
  - cloud.html
  - monitor.html
  - diagnose.html
  - diagnose_full.html

### SYSTEMD
Сервис: flask-cloud.service (активен, автозапуск)

## ЧТО РАБОТАЕТ

### АВТОРИЗАЦИЯ
- Регистрация, вход, выход
- Тестовый пользователь: admin / admin123
- Личные папки, изоляция файлов

### ОБЛАКО
- Drag-and-drop загрузка
- Множественная загрузка
- Чекбоксы, выделение всего
- Удаление и скачивание ZIP
- Сортировка, пагинация, иконки, поиск

### МОНИТОРИНГ
- Таблица метрик из БД
- Пагинация

### ДИАГНОСТИКА
- Карточки (CPU, RAM, DISK, NGINX, PostgreSQL)
- Полная диагностика каждого компонента

### NGINX
- Reverse proxy с порта 80 на 8080
- Отдача статики

### TAILSCALE
- VPN для удалённого доступа
- IP: 100.99.188.89
- SSH: ssh csn@100.99.188.89 (пароль: lab123)

### ИНФРАСТРУКТУРА
- GitHub Actions runner
- Репозиторий: github.com/csnicallyou/cloud-monitor-final
- Скрипт monitor.sh (cron каждую минуту)

## ВЫПОЛНЕННЫЕ ЗАДАЧИ
- ✅ Базовая структура Flask
- ✅ Облако (drag-and-drop, иконки, пагинация, сортировка)
- ✅ Мониторинг
- ✅ Диагностика
- ✅ Единый дизайн
- ✅ Авторизация (Flask-Login)
- ✅ Tailscale VPN
- ✅ nginx reverse proxy
- ✅ Документация (README, CHEATSHEET, INTERVIEW, PROMPT)
- ✅ Заливка на GitHub

## ОТЛОЖЕННЫЕ ЗАДАЧИ
- ⏸️ nginx + HTTPS (нужен домен)
- ⏸️ Docker + Docker Compose (пробовали, откатились)
- ❌ Grafana (отказались)
- ⏸️ Ansible (написали плейбук, но не внедрили)

## КЛЮЧЕВЫЕ КОМАНДЫ

# Статус Flask
sudo systemctl status flask-cloud

# Перезапустить Flask
sudo systemctl restart flask-cloud

# Логи Flask
sudo journalctl -u flask-cloud -n 30 --no-pager

# Обновить код из репозитория
cd /home/csn/cloud-monitor-final && git pull && cp -r cloud_app/* /home/csn/cloud_app/ && sudo systemctl restart flask-cloud

# Tailscale
tailscale ip
tailscale status

# PostgreSQL
sudo -u postgres psql -d cloud_lab

# Проверка nginx
sudo nginx -t
sudo systemctl restart nginx

## ТЕСТОВЫЕ ДАННЫЕ
- Логин: admin
- Пароль: admin123
- Сайт: http://100.99.188.89
- SSH: ssh csn@100.99.188.89 (пароль: lab123)

## ПРОБЛЕМЫ И РЕШЕНИЯ

| Проблема | Решение |
|----------|---------|
| Drag-and-drop сломался | Восстановил cloud.html с полным JS |
| nginx отдавал дефолтную страницу | Переписал конфиг, убрал экранирование |
| Flask не слушал внешние запросы | Поменял host='0.0.0.0' |
| Таблицы БД не создавались | Написал SQL-скрипт |
| 502 Bad Gateway | Создал venv и установил зависимости |
| Конфликт порта 5432 с Docker | Остановил локальный PostgreSQL |

================================================================================
КОНЕЦ ПРОМПТА
================================================================================
