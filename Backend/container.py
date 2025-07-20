# Простой DI-контейнер по аналогии с Laravel
class Container:
    def __init__(self):
        self.bindings = {}

    def bind(self, abstract, concrete):
        self.bindings[abstract] = concrete

    def resolve(self, cls):
        # Получаем список зависимостей из конструктора
        import inspect
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.values())[1:]  # исключаем self

        # Рекурсивно резолвим зависимости
        dependencies = []
        for param in params:
            dep_type = param.annotation
            if dep_type in self.bindings:
                dependency = self.resolve(self.bindings[dep_type])
            else:
                dependency = self.resolve(dep_type)
            dependencies.append(dependency)

        return cls(*dependencies)
