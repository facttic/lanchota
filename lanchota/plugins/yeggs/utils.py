DEFAULT_INSTANCE_NAME = "default"
KEYWORD_INSTANCE = 'instance_name'
KEYWORD_VALUE = 'value'
KEYWORD_CALLBACK = 'callback'


class Request(object):
    def __init__(self, instance_name=DEFAULT_INSTANCE_NAME, callback=None):
        self.callback = callback
        self.instance_name = instance_name

        super(Request, self).__init__()


class Response(object):
    def __init__(self, instance_name=DEFAULT_INSTANCE_NAME, value=None):
        if value is None:
            self.value = []
        else:
            self.value = value

        self.instance_name = instance_name

        super(Response, self).__init__()

    def render(self):
        # Explit creation of dictionary instead of self.__dict__ to avoid garbage
        return {KEYWORD_INSTANCE:self.instance_name,
                KEYWORD_VALUE:self.value}
