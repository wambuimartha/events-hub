import sys
from copy import copy
import pymysql

pymysql.install_as_MySQLdb()

# Python 3.14+ compatibility patch for Django Context copying
if sys.version_info >= (3, 14):
    try:
        from django.template import context as _ctx

        def _base_context_copy(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        def _context_copy(self):
            duplicate = _base_context_copy(self)
            duplicate.autoescape = getattr(self, 'autoescape', True)
            duplicate.use_l10n = getattr(self, 'use_l10n', None)
            duplicate.use_tz = getattr(self, 'use_tz', None)
            duplicate.template_name = getattr(self, 'template_name', 'unknown')
            duplicate.template = getattr(self, 'template', None)
            duplicate.render_context = copy(self.render_context)
            return duplicate

        def _request_context_copy(self):
            duplicate = _context_copy(self)
            duplicate.request = self.request
            duplicate._processors = self._processors
            duplicate._processors_index = self._processors_index
            return duplicate

        _ctx.BaseContext.__copy__ = _base_context_copy
        _ctx.Context.__copy__ = _context_copy
        _ctx.RequestContext.__copy__ = _request_context_copy
    except Exception:
        pass
