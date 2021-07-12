import collections
import functools
import re
import sys
import string
import os
import itertools

from . import helpers


__all__ = ('GhoStr', 'CleanGhoStr', 'ANSISGRGhoStr')


class GhoStr(collections.abc.Sequence):

    """
    A :class:`str` clone that ignores every second value yielded by
    ``disentangle``.

    Offers every behavior and method available via :class:`str` alongside the
    ones detailed bellow.

    All interactions return a plain :class:`str` object. Using :class:`str`
    returns the internal value.
    """

    __slots__ = ('_value', '_disentangle', '_mutate', '_build', '_formatter',
                 '__weakref__')

    _need_map = {
        'casefold', 'expandtabs', 'lower', 'swapcase', 'translate', 'upper'
    }

    _delegate = {'center', 'join', 'ljust', 'rjust', 'zfill'}

    _delegate_ready = {
        'count', 'endswith', 'find', 'index', 'isalnum', 'isalpha', 'isascii',
        'isdecimal', 'isdigit', 'isidentifier', 'islower', 'isnumeric',
        'isprintable', 'isspace', 'istitle', 'isupper', 'rfind', 'rindex',
        'startswith'
    }

    class _Formatter(string.Formatter):

        __slots__ = ('_disentangle',)

        def __init__(self, disentangle):

            self._disentangle = disentangle

        def _dummy(self, value):
            return (value, *(3 *(None,)))

        def _parse(self, value):
            values = self._disentangle(value)
            for (ghost, value) in helpers.inspect(values):
                if ghost:
                    yield self._dummy(value)
                    continue
                infos = super().parse(value)
                infos = tuple(infos)
                stop = len(infos) - 1
                for (index, info) in enumerate(infos):
                    yield info
                    if index == stop:
                        break
                    yield self._dummy('')
                if stop < 0:
                    yield self._dummy('')

        @helpers.methcache
        def parse(self, value):
            values = self._parse(value)
            result = tuple(values)
            return result

    def __init__(self, disentangle, value, mutate = None):

        self._value = value
        self._disentangle = disentangle
        self._mutate = mutate

        self._build = lambda value: self.__class__(disentangle, value, mutate)

        self._formatter = self._Formatter(disentangle)

    @property
    @helpers.methcache
    def _dirty(self):

        return self._disentangle(self._value)

    @property
    @helpers.methcache
    def _clean(self):

        return helpers.exclude(self._dirty)

    @property
    @helpers.methcache
    def _ready(self):

        return ''.join(self._clean)

    def _map(self, func):

        values = self._dirty

        values = helpers.map_(func, values)

        result = ''.join(values)

        return result

    def clean(self):

        """
        Remove all matches.
        """

        result = self._ready

        return result

    @helpers.methcache
    def merge(self, full = False):

        """
        Remove all sequential matches.

        For example, if ``X`` is matches, then ``'XXAXBX'`` would become
        ``'XAXBX'`` or ``'XAXB'`` if ``full``.

        This is handy for clearing leftover matches after mutation operations.
        """

        values = self._dirty

        values = helpers.clean(values, mutate = self._mutate, full = full)

        result = ''.join(values)

        return result

    def _slice(self, slice):

        values = self._dirty

        values = helpers.slice_(values, slice)

        result = ''.join(values)

        return result

    @helpers.methcache
    def _match(self, index):

        values = self._dirty

        nindex = helpers.match_index(values, index)

        result = self._value[nindex]

        count = 0
        def check(value):
            nonlocal count
            count += len(value)
            return count > index

        try:
            last = helpers.find_last(check, values)
        except ValueError:
            pass
        else:
            result = last + result

        return result

    @helpers.methcache
    def capitalize(self):

        parts = (self[:1], self[1:])

        (first, rest) = map(self._build, parts)

        return first.upper() + rest.lower()

    def _format(self, args, kwargs):

        result = self._formatter.vformat(self._value, args, kwargs)

        return result

    def format(self, *args, **kwargs):

        return self._format(args, kwargs)

    def format_map(self, mapping):

        return self._format((), mapping)

    def lstrip(self, chars = string.whitespace):

        dummy = self._ready.lstrip(chars)

        index = len(self._ready) - len(dummy)

        return self[index:]

    def maketrans(self, *args):

        func = lambda value: value.makestrans(*args)

        return self._map(func)

    def _partition(self, sep, reverse = False):

        values = (self.rsplit if reverse else self.split)(sep, 1)

        values = iter(values)

        result = [next(values)]

        try:
            result.append(next(values))
        except StopIteration:
            result.extend(('',) * 2)
            if reverse:
                result = reversed(result)
        else:
            result.insert(1, sep)

        result = tuple(result)

        return result

    def partition(self, sep):

        result = self._partition(sep)

        return result

    def removeprefix(self, prefix):

        result = self._value

        if self.startswith(prefix):
            result = self._build(result)[len(prefix):]

        return result

    def removesuffix(self, suffix):

        result = self._value

        if self.endswith(suffix):
            result = self._build(result)[:- len(suffix)]

        return result

    def replace(self, old, new, count = - 1):

        value = self

        start = 0
        while True:
            if count == 0:
                break
            try:
                index = self._ready.index(old, start)
            except ValueError:
                break
            value = value[:index] + new + value[index + len(old):]
            value = self._build(value)
            start = index + 1
            count -= 1

        return value

    def rpartition(self, sep):

        result = self._partition(sep, reverse = True)

        return result

    def _rsplit(self, sep, maxsplit, keep):

        stop = len(self._ready)

        while True:
            if maxsplit == 0:
                break
            try:
                index = self._ready.rindex(sep, 0, stop)
            except ValueError:
                break
            start = index
            if not keep:
                start += len(sep)
            start = index
            yield self[start:stop]
            stop = index
            maxsplit -= 1

        yield self[:stop]

    def rsplit(self, sep = ' ', maxsplit = - 1):

        result = self._rsplit(sep, maxsplit, False)

        result = list(reversed(tuple(result)))

        return result

    def rstrip(self, chars = string.whitespace):

        dummy = self._ready.rstrip(chars)

        index = len(dummy)

        return self[:index]

    def _split(self, sep, maxsplit, keep):

        start = 0

        while True:
            if maxsplit == 0:
                break
            try:
                index = self._ready.index(sep, start)
            except ValueError:
                break
            stop = index
            if keep:
                stop += len(sep)
            yield self[start:stop]
            start = index + len(sep)
            maxsplit -= 1

        yield self[start:]

    def split(self, sep = ' ', maxsplit = - 1):

        result = self._split(sep, maxsplit, False)

        result = list(result)

        return result

    def splitlines(self, keepends = False):

        result = self._split(os.linesep, - 1, keepends)

        result = list(result)

        return result

    def strip(self, chars = string.whitespace):

        return self._build(self.lstrip(chars)).rstrip(chars)

    def _title(self):

        for part in self._split(' ', - 1, True):
            yield self._build(part).capitalize()

    def title(self):

        result = self._title()

        result = ''.join(result)

        return result

    @helpers.methcache
    def __getattr__(self, key):

        pairs = (
            (self._delegate, self._value),
            (self._delegate_ready, self._ready)
        )
        for (keys, value) in pairs:
            if not key in keys:
                continue
            break
        else:
            value = None

        if value is None:
            result = getattr(str, key)
            if key in self._need_map:
                result = functools.partial(self._map, result)
        else:
            result = getattr(value, key)

        return result

    def __str__(self):

        return self._value

    def __repr__(self):

        return repr(self._value)

    def __int__(self):

        return int(self._ready)

    def __float__(self):

        return float(self._ready)

    def __complex__(self):

        return complex(self._ready)

    def __hash__(self):

        return hash(self._value)

    def __eq__(self, other):

        return str(self) == str(other)

    def __ne__(self, other):

        return not self == other

    def __lt__(self, other):

        return str(self) < str(other)

    def __le__(self, other):

        return self == other or self < other

    def __gt__(self, other):

        return str(self) > str(other)

    def __ge__(self, other):

        return self == other or self < other

    def __contains__(self, sub):

        return sub in self._ready

    def __len__(self):

        return len(self._ready)

    def __getitem__(self, arg):

        isslice = isinstance(arg, slice)

        return (self._slice if isslice else self._match)(arg)

    def __add__(self, other):

        return self._value + str(other)

    def __radd__(self, other):

        return str(other) + self._value

    def __mul__(self, value):

        return self._value * value

    def __rmul__(self, value):

        return self.__mul__(value)

    def __mod__(self, args):

        raise NotImplementedError('use format')

    def __rmod__(self, value):

        raise NotImplementedError('use format')

    def __format__(self, value):

        return format(self._value, value)

    def __iter__(self):

        return iter(self._ready)

    def __reversed__(self):

        return reversed(self._ready)

    def __sizeof__(self):

        return sys.getsizeof(self._value)


class CleanGhoStr(GhoStr):

    """
    Just like its parent, but attempts to keep sequential matches at a minimal.
    """

    __slots__ = ()

    def _smuge(self, result):

        return self._build(result).merge()

    def _slice(self, *args, **kwargs):

        result = super()._slice(*args, **kwargs)

        return self._smuge(result)

    def _format(self, *args, **kwargs):

        result = super()._format(*args, **kwargs)

        return self._smuge(result)

    def __add__(self, *args, **kwargs):

        result = super().__add__(*args, **kwargs)

        return self._smuge(result)

    def __radd__(self, *args, **kwargs):

        result = super().__radd__(*args, **kwargs)

        return self._smuge(result)

    def __mul__(self, *args, **kwargs):

        result = super().__mul__(*args, **kwargs)

        return self._smuge(result)


@functools.lru_cache(1)
def _re_split(pattern):

    pattern = '({0})'.format(pattern)

    split = re.compile(pattern).split

    return split


_ansi_sgr_split = _re_split('\x1b[\\[0-?]*m')


_ansi_sgr_null = '\x1b[0m'


_ansi_sgr_groups = tuple(
    set(map(str, itertools.chain.from_iterable(ranges)))
    for ranges
    in (
        ((1, 21, 22),),
        ((2, 22,),),
        ((3, 23),),
        ((4, 24),),
        ((5, 25),),
        ((6, 25),),
        ((7, 27),),
        ((8, 28),),
        ((9, 29),),
        ((10,), range(11, 20)),
        ((20, 23),),
        (range(30, 40), range(90, 98)),
        (range(40, 50), range(100, 108)),
        ((26, 50),)
        ((51, 54),),
        ((52, 54),),
        ((53, 55),)
        ((58, 59),)
    )
)


def _check_sgr_group_family(code0, code1, groups = _ansi_sgr_groups):

    for group in groups:
        if not (code0 in group and code1 in group):
            continue
        break
    else:
        return False

    return True


del _ansi_sgr_groups


def _ansi_sgr_mutate(last, next, family = _check_sgr_group_family):

    if not last:
        last.append(next)
        return

    if next == _ansi_sgr_null:
        last.clear()

    ncode = helpers.get_ansi_sgr_code(next)

    index = 0
    while True:
        try:
            value = last[index]
        except IndexError:
            break
        lcode = helpers.get_ansi_sgr_code(value)
        if family(ncode, lcode):
            del last[index]
            continue
        index += 1

    last.append(next)


del _check_sgr_group_family


class ANSISGRGhoStr(CleanGhoStr):

    """
    Used to handle `ANSI SGR
    <https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters>`_ sequences.

    Formatting respects pre-placeholder attributes and continues them.

    Merging does not rid of sequences that have overlapping effects.
    """

    __slots__ = ()

    class _Formatter(GhoStr._Formatter):

        __slots__ = ()

        def _smear(self, infos):
            last = []
            for (ghost, info) in helpers.inspect(infos):
                yield info
                if ghost:
                    last.append(info[0])
                    continue
                name = info[1]
                if not name is None:
                    final = _ansi_sgr_null + ''.join(last)
                    yield self._dummy(final)

        @helpers.methcache
        def parse(self, value):
            infos = super().parse(value)
            infos = self._smear(infos)
            result = tuple(infos)
            return result

    def __init__(self, value):

        super().__init__(_ansi_sgr_split, value, _ansi_sgr_mutate)

        self._build = lambda value: self.__class__(value)

    def merge(self, full = True):

        return super().merge(full)
