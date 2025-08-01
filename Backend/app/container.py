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
    
    def resolve(self, service_type: Type) -> Any:
    # Проверяем, есть ли уже созданный синглтон
        if service_type in self.singletons:
            return self.singletons[service_type]
        
        descriptor = self.services.get(service_type)
        if descriptor is None:
            raise Exception(f"Service {service_type} not registered")
        
        # Создаем экземпляр с учетом фабричной функции
        if descriptor.factory_func is not None:
            instance = descriptor.factory_func()
        else:
            # Создаем экземпляр, автоматически передавая зависимости через конструктор
            instance = self._create_instance(descriptor.implementation)
        
        # Сохраняем синглтон, если нужно
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            self.singletons[service_type] = instance
        
        return instance

    def _create_instance(self, cls: Type) -> Any:
        # Анализируем конструктор
        signature = inspect.signature(cls.__init__)
        # Все параметры кроме self
        params = list(signature.parameters.values())[1:]
        
        # Для каждого параметра пытаемся разрешить зависимость по аннотации
        args = []
        for param in params:
            if param.annotation == inspect.Parameter.empty:
                raise Exception(f"Cannot resolve dependency '{param.name}' of {cls}")
            dependency = self.resolve(param.annotation)
            args.append(dependency)
        
        return cls(*args)
