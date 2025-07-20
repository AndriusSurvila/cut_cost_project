# app/policies/policies.py
from abc import ABC, abstractmethod
from typing import Any, Optional
from fastapi import HTTPException, status

class BasePolicy(ABC):
    """Базовый класс для всех политик авторизации"""
    
    def __init__(self, user: Optional[dict] = None):
        self.user = user
    
    def is_authenticated(self) -> bool:
        """Проверяет, аутентифицирован ли пользователь"""
        return self.user is not None
    
    def is_owner(self, resource: dict) -> bool:
        """Проверяет, является ли пользователь владельцем ресурса"""
        if not self.is_authenticated():
            return False
        return resource.get('user_id') == self.user.get('id')
    
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if not self.is_authenticated():
            return False
        return self.user.get('role') == 'admin'
    
    def deny(self, message: str = "Access denied"):
        """Вызывает исключение с отказом в доступе"""
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )
    
    def authorize(self, action: str, resource: Any = None):
        """Основной метод авторизации"""
        method_name = f"can_{action}"
        if hasattr(self, method_name):
            policy_method = getattr(self, method_name)
            if not policy_method(resource):
                self.deny(f"You are not authorized to {action}")
        else:
            self.deny(f"Policy method {method_name} not implemented")

    @abstractmethod
    def can_view(self, resource: Any = None) -> bool:
        pass
    
    @abstractmethod
    def can_create(self, resource: Any = None) -> bool:
        pass
    
    @abstractmethod
    def can_update(self, resource: Any = None) -> bool:
        pass
    
    @abstractmethod
    def can_delete(self, resource: Any = None) -> bool:
        pass


class UserPolicy(BasePolicy):
    """Политики авторизации для пользователей"""
    
    def can_view(self, resource: Optional[dict] = None) -> bool:
        """Может ли пользователь просматривать данные"""
        if not self.is_authenticated():
            return False
        
        # Администратор может видеть всех пользователей
        if self.is_admin():
            return True
        
        # Пользователь может видеть только свой профиль
        if resource:
            return self.is_owner(resource)
        
        # Если ресурс не указан, разрешаем (список пользователей для админа)
        return True
    
    def can_create(self, resource: Optional[dict] = None) -> bool:
        """Может ли создавать пользователей"""
        # Создавать пользователей может только администратор
        return self.is_admin()
    
    def can_update(self, resource: Optional[dict] = None) -> bool:
        """Может ли обновлять данные пользователя"""
        if not self.is_authenticated():
            return False
        
        # Администратор может обновлять любого пользователя
        if self.is_admin():
            return True
        
        # Пользователь может обновлять только свои данные
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_delete(self, resource: Optional[dict] = None) -> bool:
        """Может ли удалять пользователя"""
        if not self.is_authenticated():
            return False
        
        # Удалять пользователей может только администратор
        if self.is_admin():
            return True
        
        # Пользователь может удалить только свой аккаунт
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_view_sensitive_data(self, resource: Optional[dict] = None) -> bool:
        """Может ли видеть чувствительные данные пользователя"""
        if not self.is_authenticated():
            return False
        
        # Администратор видит всё
        if self.is_admin():
            return True
        
        # Пользователь видит только свои чувствительные данные
        if resource:
            return self.is_owner(resource)
        
        return False


class ChatPolicy(BasePolicy):
    """Политики авторизации для чатов"""
    
    def can_view(self, resource: Optional[dict] = None) -> bool:
        """Может ли пользователь просматривать чат"""
        if not self.is_authenticated():
            return False
        
        # Администратор может видеть все чаты
        if self.is_admin():
            return True
        
        # Пользователь может видеть свои чаты
        if resource:
            return self.is_owner(resource) or self._is_chat_participant(resource)
        
        return True  # Для списка собственных чатов
    
    def can_create(self, resource: Optional[dict] = None) -> bool:
        """Может ли создавать чаты"""
        # Любой аутентифицированный пользователь может создать чат
        return self.is_authenticated()
    
    def can_update(self, resource: Optional[dict] = None) -> bool:
        """Может ли обновлять чат"""
        if not self.is_authenticated():
            return False
        
        # Администратор может обновлять любой чат
        if self.is_admin():
            return True
        
        # Владелец чата может его обновлять
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_delete(self, resource: Optional[dict] = None) -> bool:
        """Может ли удалять чат"""
        if not self.is_authenticated():
            return False
        
        # Администратор может удалять любой чат
        if self.is_admin():
            return True
        
        # Владелец чата может его удалить
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_send_message(self, resource: Optional[dict] = None) -> bool:
        """Может ли отправлять сообщения в чат"""
        if not self.is_authenticated():
            return False
        
        # Администратор может писать в любой чат
        if self.is_admin():
            return True
        
        # Участник чата может отправлять сообщения
        if resource:
            return self.is_owner(resource) or self._is_chat_participant(resource)
        
        return False
    
    def can_view_messages(self, resource: Optional[dict] = None) -> bool:
        """Может ли просматривать сообщения чата"""
        if not self.is_authenticated():
            return False
        
        # Администратор может читать любые сообщения
        if self.is_admin():
            return True
        
        # Участник чата может читать сообщения
        if resource:
            return self.is_owner(resource) or self._is_chat_participant(resource)
        
        return False
    
    def _is_chat_participant(self, chat: dict) -> bool:
        """Проверяет, является ли пользователь участником чата"""
        participants = chat.get('participants', [])
        user_id = self.user.get('id')
        return user_id in participants


class MessagePolicy(BasePolicy):
    """Политики авторизации для сообщений"""
    
    def can_view(self, resource: Optional[dict] = None) -> bool:
        """Может ли просматривать сообщение"""
        if not self.is_authenticated():
            return False
        
        # Администратор может видеть любые сообщения
        if self.is_admin():
            return True
        
        # Владелец сообщения может его видеть
        if resource and self.is_owner(resource):
            return True
        
        # Участник чата может видеть сообщения в этом чате
        if resource and 'chat' in resource:
            chat = resource['chat']
            participants = chat.get('participants', [])
            return self.user.get('id') in participants
        
        return False
    
    def can_create(self, resource: Optional[dict] = None) -> bool:
        """Может ли создавать сообщения"""
        # Любой аутентифицированный пользователь может создать сообщение
        # (если он участник чата - это проверяется в контроллере)
        return self.is_authenticated()
    
    def can_update(self, resource: Optional[dict] = None) -> bool:
        """Может ли редактировать сообщение"""
        if not self.is_authenticated():
            return False
        
        # Администратор может редактировать любые сообщения
        if self.is_admin():
            return True
        
        # Владелец сообщения может его редактировать
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_delete(self, resource: Optional[dict] = None) -> bool:
        """Может ли удалять сообщение"""
        if not self.is_authenticated():
            return False
        
        # Администратор может удалять любые сообщения
        if self.is_admin():
            return True
        
        # Владелец сообщения может его удалить
        if resource and self.is_owner(resource):
            return True
        
        # Владелец чата может удалять сообщения в своем чате
        if resource and 'chat' in resource:
            chat = resource['chat']
            return chat.get('user_id') == self.user.get('id')
        
        return False


class FilePolicy(BasePolicy):
    """Политики авторизации для файлов"""
    
    def can_view(self, resource: Optional[dict] = None) -> bool:
        """Может ли просматривать файл"""
        if not self.is_authenticated():
            return False
        
        # Администратор может видеть любые файлы
        if self.is_admin():
            return True
        
        # Владелец файла может его видеть
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_create(self, resource: Optional[dict] = None) -> bool:
        """Может ли загружать файлы"""
        # Любой аутентифицированный пользователь может загружать файлы
        return self.is_authenticated()
    
    def can_update(self, resource: Optional[dict] = None) -> bool:
        """Может ли обновлять файл"""
        if not self.is_authenticated():
            return False
        
        # Администратор может обновлять любые файлы
        if self.is_admin():
            return True
        
        # Владелец файла может его обновлять
        if resource:
            return self.is_owner(resource)
        
        return False
    
    def can_delete(self, resource: Optional[dict] = None) -> bool:
        """Может ли удалять файл"""
        if not self.is_authenticated():
            return False
        
        # Администратор может удалять любые файлы
        if self.is_admin():
            return True
        
        # Владелец файла может его удалить
        if resource:
            return self.is_owner(resource)
        
        return False


# Фабрика для создания политик
class PolicyFactory:
    """Фабрика для создания экземпляров политик"""
    
    @staticmethod
    def create_policy(policy_type: str, user: Optional[dict] = None) -> BasePolicy:
        """Создает политику по типу"""
        policies = {
            'user': UserPolicy,
            'chat': ChatPolicy,
            'message': MessagePolicy,
            'file': FilePolicy,
        }
        
        policy_class = policies.get(policy_type.lower())
        if not policy_class:
            raise ValueError(f"Unknown policy type: {policy_type}")
        
        return policy_class(user)
    
    @staticmethod
    def get_available_policies() -> list:
        """Возвращает список доступных типов политик"""
        return ['user', 'chat', 'message', 'file']