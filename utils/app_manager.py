import json
import os
from typing import Dict, List
from datetime import datetime

class AppManager:
    def __init__(self, apps_dir: str):
        self.apps_dir = apps_dir
        self.apps: Dict[str, dict] = {}
        self.load_apps()

    def load_apps(self):
        """Загрузка всех приложений из директории"""
        for filename in os.listdir(self.apps_dir):
            if filename.endswith('.json'):
                app_id = os.path.splitext(filename)[0]
                with open(os.path.join(self.apps_dir, filename), 'r', encoding='utf-8') as f:
                    self.apps[app_id] = json.load(f)

    def get_app(self, app_id: str) -> dict:
        """Получение информации о приложении"""
        return self.apps.get(app_id, {})

    def get_apps_for_user(self, user_role: str) -> List[dict]:
        """Получение списка приложений доступных для пользователя"""
        return [
            app for app in self.apps.values()
            if user_role in app.get('access', {}).get('roles', [])
        ]

    def update_app_stats(self, app_id: str, stats: dict):
        """Обновление статистики приложения"""
        if app_id in self.apps:
            self.apps[app_id]['stats'].update(stats)
            self.save_app(app_id)

    def save_app(self, app_id: str):
        """Сохранение информации о приложении"""
        with open(os.path.join(self.apps_dir, f"{app_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(self.apps[app_id], f, ensure_ascii=False, indent=2)

    def validate_user_access(self, user_role: str, app_id: str, permission: str) -> bool:
        """Проверка прав доступа пользователя к приложению"""
        app = self.get_app(app_id)
        if not app:
            return False
            
        access = app.get('access', {})
        return (
            user_role in access.get('roles', []) and
            access.get('permissions', {}).get(permission, False)
        )
