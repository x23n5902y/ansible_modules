class DsmsysOperations():
    def __init__(self, obj):
        self.statements = obj

    def read(self):
        return self.statements

    def section_delete(self, section_name):
        if self.statements.get(section_name):
            self.statements.pop(section_name, None)
        return self.statements

    def statement_delete(self, section_name, statement):
        if self.statements.get(section_name) \
                and self.statements[section_name].get(statement):
            self.statements[section_name].pop(statement, None)
        return self.statements

    def section_update(self, section_name, new_section_name):
        if self.statements.get(section_name) or self.statements.get(section_name) == {}:
            self.statements[new_section_name] = self.statements.pop(section_name)
        return self.statements

    def statement_update(self, section_name, statement, value):
        if self.statements.get(section_name) \
                and self.statements[section_name].get(statement):
            self.statements[section_name][statement] = value
            return self.statements
        return self.statements

    def section_create(self, section_name):
        if self.statements.get(section_name):
            return self.statements
        self.statements[section_name] = {}
        return self.statements

    def statement_create(self, section_name, statement, value):
        if not self.statements.get(section_name):
            self.section_create(section_name)
        self.statements[section_name][statement] = value
        return self.statements

    def section_read(self, section_name):
        if self.statements.get(section_name):
            return self.statements.get(section_name)
        return None

    def statement_read(self, section_name, statement):
        if self.statements.get(section_name) \
                and self.statements[section_name].get(statement):
            return self.statements[section_name].get(statement)
        return None

    @property
    def stanza(self):
        return Stanza(self)

    @property
    def option(self):
        return Option(self)


class Stanza():
    def __init__(self, *args):
        self.stanza = args[0]

    def create(self, *args, **kwargs):
        if self.__args(*args, **kwargs):
            return self.stanza.section_create(*self.__args(*args, **kwargs))

    def read(self, *args, **kwargs):
        if self.__args(*args, **kwargs):
            return self.stanza.section_read(*self.__args(*args, **kwargs))

    def update(self, *args, **kwargs):
        if self.__args(*args, **kwargs):
            return self.stanza.section_update(*self.__args(*args, **kwargs))

    def delete(self, *args, **kwargs):
        if self.__args(*args, **kwargs):
            return self.stanza.section_delete(*self.__args(*args, **kwargs))

    def __args(self, *args, **kwargs):
        if kwargs.get('name'):
            return [kwargs.get('name').upper()]

        if args:
            return args
        return None


class Option():
    def __init__(self, *args):
        self.option = args[0]

    def create(self, *args, **kwargs):
        if self.__args(*args, **kwargs) and len(self.__args(*args, **kwargs)) == 3:
            return self.option.statement_create(*self.__args(*args, **kwargs))

    def read(self, *args, **kwargs):
        if self.__args(*args, **kwargs) and len(self.__args(*args, **kwargs)) == 2:
            return self.option.statement_read(*self.__args(*args, **kwargs))

    def update(self, *args, **kwargs):
        if self.__args(*args, **kwargs) and len(self.__args(*args, **kwargs)) == 3:
            return self.option.statement_update(*self.__args(*args, **kwargs))

    def delete(self, *args, **kwargs):
        if self.__args(*args, **kwargs) and len(self.__args(*args, **kwargs)) == 2:
            return self.option.statement_delete(*self.__args(*args, **kwargs))

    def __args(self, *args, **kwargs):
        if kwargs.get('name') and kwargs.get('option'):
            if kwargs.get('value'):
                return [kwargs.get('name'),
                        kwargs.get('option').upper(),
                        kwargs.get('value')]
            return [kwargs.get('name'),
                    kwargs.get('option').upper()]

        if args:
            _ = list(args)
            if _[1]:
                _[1] = _[1].upper()
            args = tuple(_)
            return args
        return None
