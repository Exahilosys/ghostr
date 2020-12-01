import sys
import functools
import weakref


__all__ = ()


if sys.version_info < (3, 9):
    _cache_func = lambda func: functools.lru_cache(None)(func)
else:
    _cache_func = functools.cache


def methcache(func, cache = weakref.WeakKeyDictionary()):

    def _get(self):
        try:
            ccache = cache[self]
        except KeyError:
            ccache = cache[self] = {}
        try:
            cfunc = ccache[func]
        except KeyError:
            wself = weakref.ref(self)
            def pfunc(*args, **kwargs):
                return func(wself(), *args, **kwargs)
            cfunc = ccache[func] = _cache_func(pfunc)
        return cfunc

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        cfunc = _get(self)
        return cfunc(*args, **kwargs)

    return wrapper


def _is_ghost(index):

    return index % 2


def inspect(values):

    for (index, value) in enumerate(values):
        yield (_is_ghost(index), value)


def exclude(values):

    for (ghost, value) in inspect(values):
        if ghost or not value:
            continue
        yield value


def _measure(values):

    return sum(map(len, exclude(values)))


def map_(func, values):

    for (ghost, value) in inspect(values):
        if not ghost:
            value = func(value)
        yield value


def slice_(values, slice):

    size = _measure(values)

    (start, stop, step) = slice.indices(size)

    limit = stop - start

    point = 0
    carry = 0
    for (ghost, value) in inspect(values):
        if ghost:
            yield value
            continue
        if not point < stop:
            continue
        size = len(value)
        point += size
        if point < start:
            continue
        excess = size - point
        limit = excess + start
        vstart = limit if limit > 0 else carry
        vstop = excess + stop
        carry = size % step
        yield value[vstart:vstop:step]


def _progressive_rid(last, next):

    try:
        del last[0]
    except IndexError:
        pass

    last.append(next)


def clean(values, mutate = None, full = False):

    if not mutate:
        mutate = _progressive_rid

    last = []
    for (index, (ghost, value)) in enumerate(inspect(values)):
        if ghost:
            mutate(last, value)
            continue
        if value:
            yield from last
            yield value
            last.clear()

    if full:
        yield from last


def match_index(values, fake):

    if fake < 0:
        size = _measure(values)
        fake = size + fake

    real = 0
    for (ghost, value) in inspect(values):
        if ghost:
            real += len(value)
            continue
        size = len(value)
        real += min(size, fake)
        fake -= size
        if fake < 0:
            break

    return real


def parse_ansi(value, csi = '\x1b', code = 'm'):

    value = value[len(csi):-len(code)]

    value = value.removeprefix('[')

    info = value.split(';')

    return info


def get_ansi_sgr_code(value):

    info = parse_ansi(value)

    return info[0] if info else '0'
