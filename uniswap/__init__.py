# Python 3.14 compatibility patch for django.template.context.BaseContext.__copy__
try:
    import copy
    from django.template import context as _dtc

    def _safe_base_context_copy(self):
        obj = self.__class__.__new__(self.__class__)
        obj.__dict__.update(self.__dict__)
        obj.dicts = self.dicts[:]
        return obj

    _dtc.BaseContext.__copy__ = _safe_base_context_copy
except Exception:
    pass

