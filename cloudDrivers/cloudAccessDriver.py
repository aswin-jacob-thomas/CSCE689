import abc

class cloudDriver(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'initialize') and 
                callable(subclass.initialize) and 
                hasattr(subclass, 'write') and 
                callable(subclass.write)) and
                hasattr(subclass, 'read') and 
                callable(subclass.read)

