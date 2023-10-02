from .converter import Converter

class Param:
    '''Param is a class that stores info for input/output of an atom.'''
    def __init__(self, prompt, expected_type:type, converter=None, default=None):
        '''
        :param prompt: The prompt for searching.
        :param expected_type: The expected type of the input/output.
        :param converter: The converter for converting the input/output. If not specified, will try to convert the input/output to the expected type.
        :param default: default value for the input/output when type conversion failed.
        '''
        self.prompt = prompt
        self.expected_type = expected_type
        self.converter = converter
        self.default = default
        self._value = None # store the value of the param

    def input(self, value):
        if isinstance(value, self.expected_type): # no need to convert
            self._value = value
        else: # try to convert
            try:
                if self.converter is not None:
                    self._value = self.converter(value)
                else:
                    try:
                        converter = Converter[self.expected_type]
                        self._value = converter.convert(value)
                    except KeyError:
                        self._value = self.expected_type(value)
            except:
                self._value = self.default

    @property
    def value(self):
        return self._value if self._value is not None else self.default