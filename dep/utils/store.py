class DictStorage(dict):
    def __init__(self, update_func):
        super().__init__()
        self.update_func = update_func

    def __getitem__(self, key):
        if not self:
            self.update()

        return super().__getitem__(key)

    def __iter__(self):
        if not self:
            self.update()

        return super().__iter__()

    def __str__(self):
        if not self:
            self.update()

        return super().__str__()

    def values(self):
        if not self:
            self.update()

        return super().values()

    def keys(self):
        if not self:
            self.update()

        return super().keys()

    def get(self, key, default=None):
        if not self:
            self.update()

        return super().get(key, default)

    def update(self):
        self.update_func(self)
