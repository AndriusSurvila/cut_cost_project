from typing import Dict, Any, Type, Optional
import inspect
from enum import Enum

class ServiceLifetime(Enum):
    """Время жизни сервиса"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class ServiceDescriptor:
    """Дескриптор сервиса"""
    def __init__(
        self, 
        service_type: Type, 
        implementation: Type, 
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory_func: Optional[callable] = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory_func = factory_func

class EnhancedContainer:
    """Улучшенный DI контейнер с поддержкой времени жизни"""
    
    def __init__(self):
        self.services: Dict[Type, ServiceDescriptor] = {}
        self.singletons: Dict[Type, Any] = {}
        self.scoped_instances: Dict[Type, Any] = {}
    
    def register_singleton(self, service_type: Type, implementation: Type):
        """Регистрация сервиса как синглтон"""
        self.services[service_type] = ServiceDescriptor(
            service_type, implementation, ServiceLifetime.SINGLETON
        )
        return self
    
    def register_transient(self, service_type: Type, implementation: Type):
        """Регистрация сервиса как транзиентный"""
        self.services[service_type] = ServiceDescriptor(
            service_type, implementation, ServiceLifetime.TRANSIENT
        )
        return self
    
    def register_scoped(self, service_type: Type, implementation: Type):
        """Регистрация сервиса в области видимости"""
        self.services[service_type] = ServiceDescriptor(
            service_type, implementation, ServiceLifetime.SCOPED
        )
        return self
    
    def register_factory(
        self, 
        service_type: Type, 
        factory_func: callable,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ):
        """Регистрация фабричного метода"""
        self.services[service_type] = ServiceDescriptor(
            service_type, None, lifetime, factory_func
        )
        return self
    
    def register_instance(self, service_type: Type, instance: Any):
        """Регистрация готового экземпляра"""
        self.singletons[service_type] = instance
        return self