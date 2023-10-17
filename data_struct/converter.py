from utils.global_value_utils import GetOrAddGlobalValue
import re
from typing import Sequence

# region Converter base class
_CONVERTER_CLSES = GetOrAddGlobalValue('_CONVERTER_CLSES', dict()) # type : converter
_INITED_CONVERTER_CLSES = GetOrAddGlobalValue('_INITED_CONVERTER_CLSES', dict()) # cls_name : converter
class ConverterMeta(type):
    def __new__(self, *args, **kwargs):
        cls_name = args[0]
        if cls_name != 'Converter' and cls_name not in _INITED_CONVERTER_CLSES:
            cls = super().__new__(self, *args, **kwargs)
            if cls.type_name() not in _CONVERTER_CLSES:
                _CONVERTER_CLSES[cls.type_name()] = cls # only save the first converter of this type
            _INITED_CONVERTER_CLSES[cls_name] = cls
            return cls
        if cls_name == 'Converter':
            return super().__new__(self, *args, **kwargs)
        else:
            return _CONVERTER_CLSES[cls_name] # return the existed converter
class Converter(metaclass=ConverterMeta):
    '''
    Converter is those static classes for converting value to specific type.
    This is the base class of all converters.
    Converter classes not allow to have same class name.
    '''

    def __class_getitem__(cls, item):
        """You can access the converter by Converter[type]."""
        if isinstance(item,type):
            try:
                item = item.__qualname__
            except:
                item = item.__name__
        try:
            return _CONVERTER_CLSES[item]
        except:
            raise KeyError(f'Converter with output type:{item} is not implemented.')
    def __init__(self):
        raise Exception("Converter is a static class, don't initialize it. You cound use Converter['type'] to get the converter with output type.")

    @classmethod
    def type_name(cls):
        try:
            return cls.type().__qualname__
        except:
            return cls.type().__name__

    @classmethod
    def type(self):
        '''override this method to specify the output type of the converter'''
        raise NotImplementedError
    @classmethod
    def convert(cls, value):
        '''override this method to specify the convert method. Note that input value can be any type.'''
        raise NotImplementedError
# endregion

# region number converters
class IntConverter(Converter):
    @classmethod
    def type(cls):
        return int
    @classmethod
    def convert(cls, value):
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            value = value.strip()
            if str.isdigit(value):
                return int(value)
            # try match the first int
            match = re.match(r'(-?\d+)', value)
            if match is not None:
                return int(match.group(1))
            raise ValueError(f'Cannot convert {value} to int')
        try:
            return int(value)
        except:
            raise ValueError(f'Cannot convert {value} to int')
class FloatConverter(Converter):
    @classmethod
    def type(cls):
        return float
    @classmethod
    def convert(cls, value):
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            value = value.strip()
            if str.isdigit(value):
                return float(value)
            # try match the first float
            match = re.match(r'(-?\d+\.?\d*)', value)
            if match is not None:
                return float(match.group(1))
            raise ValueError(f'Cannot convert {value} to float')
        try:
            return float(value)
        except:
            raise ValueError(f'Cannot convert {value} to float')
# endregion

# region sequence converters
class ListConverter(Converter):
    @classmethod
    def type(cls):
        return list
    @classmethod
    def convert(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # if [..] or (..) is found, use re to extract the sub string
            if re.match(r'\s*\[.*\]\s*$', value) or re.match(r'\s*\{.*\}\s*$', value) or re.match(r'\s*\((.*)\)\s*$', value):
                value = re.search(r'\[.*\]|\{.*\}|\((.*)\)', value).group()[1:-1]
            result = re.split(r'\s*,\s*', value)
            if len(result) == 1:
                if result[0] == '':
                    return []
                if ' ' in result[0]:
                    return result[0].split(' ')
            return result
        if isinstance(value, Sequence):
            return list(value)
        try:
            return list(value)
        except:
            raise ValueError(f'Cannot convert {value} to list')
class NumListConverter(Converter):
    @classmethod
    def type(cls):
        return list
    @classmethod
    def convert(cls, value):
        value = ListConverter.convert(value)
        return [FloatConverter.convert(v) for v in value]
class IntListConverter(Converter):
    @classmethod
    def type(cls):
        return list
    @classmethod
    def convert(cls, value):
        value = ListConverter.convert(value)
        return [IntConverter.convert(v) for v in value]
# endregion

class BoolConverter(Converter):
    @classmethod
    def type(cls):
        return bool
    @classmethod
    def convert(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.strip().lower()
            if 'true' in value:
                return True
            if 'false' in value:
                return False
            if str.isdigit(value):
                return bool(int(value))
            else:
                try:
                    return bool(float(value))
                except ValueError:
                    pass
            raise ValueError(f'Cannot convert {value} to bool')
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, float):
            return bool(value)
        try:
            return bool(value)
        except:
            raise ValueError(f'Cannot convert {value} to bool')

class StrConverter(Converter):
    @classmethod
    def type(cls):
        return str
    @classmethod
    def convert(cls, value):
        if isinstance(value, str):
            return value
        try:
            return str(value)
        except:
            raise ValueError(f'Cannot convert {value} to str')

class DictConverter(Converter):
    @classmethod
    def type(cls):
        return dict
    @classmethod
    def convert(cls, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            pass
        try:
            return dict(value)
        except:
            raise ValueError(f'Cannot convert {value} to dict')

