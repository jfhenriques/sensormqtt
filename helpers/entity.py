

class Entity(object):

    def __init__(self, uuid, name, mqtt_topic = None):
        self.__uuid: str = uuid
        self.__name: str = name
        self.__mqtt_topic: str = mqtt_topic

    def get_uuid(self) -> str:
        return self.__uuid
    
    def get_name(self) -> str:
        return self.__name

    def get_mqtt_topic(self) -> str:
        return self.__mqtt_topic