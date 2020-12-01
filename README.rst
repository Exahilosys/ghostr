Strings that ignore part of themselves.

.. image:: https://github.com/Exahilosys/ghostr/raw/master/images/showcase.png

.. code-block:: py

    from ghostr import ANSISGRGhoStr as gstr

    test = '\x1b[38;5;6mHello\x1b[38;5;10m there! Th\x1b[38;5;9mis is \x1b[7ma {0} demon\x1b[90mstration of the libr\x1b[0mary\'s \x1b[38;5;12m\x1b[4mcapabilities\x1b[0m!'
    print('1)', test)
    test = gstr(test).format('\x1b[3m\x1b[38;5;11mcool')
    print('2)', test)
    test = gstr(test)[:21] + gstr(test)[45:]
    print('3)', test)

Installing
----------

.. code-block::

    pip3 install survey

Links
-----

- Check out the `documentation <https://ghostr.readthedocs.io>`_ for more info.
