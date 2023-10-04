'''Decorator to build a deferrable functions.'''

class DeferrableFunc:
    '''
    Decorator to build a deferrable functions.
    ::
        @DeferrableFunc
        def func():
             DeferableFunc.defer(lambda: print('deferred'))
             print('func')
        func() # print 'func' then 'deferred'
    '''

    _deferringFunc: 'DeferrableFunc' = None
    _defers: list = []

    def __init__(self, func):
        self._func = func

    def __enter__(self):
        self.__class__._deferringFunc = self
        self.__class__._defers.clear()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        for defer in self.__class__._defers[::-1]:
            defer()
        self.__class__._deferringFunc = None
        self.__class__._defers.clear()
    def __call__(self, *args, **kwargs):
        with self:
            ret = self._func(*args, **kwargs)
        return ret

    @classmethod
    def defer(cls, lambdaFunc):
        if cls._deferringFunc is None:
            raise Exception('DeferrableFunc.defer can only be called during the execution of DeferrableFunc')
        cls._defers.append(lambdaFunc)

