# Agent-Spies Bot

Este es un bot de Discord creado para la gestión de usuarios y moderación en un servidor.

## Requisitos

- Python 3.x
- discord.py
- python-dotenv
- requests

## Instalación

1. Clona este repositorio.
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno virtual: `source venv/bin/activate` (Linux/Mac) o `venv\Scripts\activate` (Windows)
4. Instala las dependencias: `pip install -r requirements.txt`
5. Crea un archivo `.env` con el token de tu bot.
6. Ejecuta el bot: `python bot.py`

## Comandos

- `!ping`: Responde con "Pong!"
- `!warn @user reason`: Advierte a un usuario.
- `!ban @user reason`: Banea a un usuario.
- `!userinfo @user`: Muestra la información del usuario.
