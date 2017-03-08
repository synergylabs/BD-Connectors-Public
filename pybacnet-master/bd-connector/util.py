"""
    util.py
    ~~~~~~~~~~~~~~

    Various helper functions and tools used throughout different
    code repos

    @copyright:	(c) 2014 SynergyLabs
    @license:	UCSD License. See License file for details.
    @authors: bbalaji@ucsd.edu
"""

import re

_digits = re.compile('\d')
def contains_digits(d):
    return bool(_digits.search(d))