#!/usr/bin/python3

"""
    samba feeds writting module
    (C) 2018 Martin Tomasek
    (C) 2018 DiffSolutions s.r.o.
    Licensed under CC BY-SA 4.0

"""

from lxml.etree import tostring

class Feed(object):
    def __init__(self, name, fname, tag):
        self.f = f = open(fname, "wb+")
        self.name = name
        self.tag = tag
        self.header()

    def __exit__(self, typ, val, tb):
        self.close()

    def __enter__(self):
        return self

    def close(self):
        self.footer()
        self.f.close()

    def header(self):
        self.f.write('''<?xml version="1.0"
                     encoding="utf-8"?>\n<{}>\n'''.format(self.tag).encode("UTF-8"))

    def footer(self):
        self.f.write("</{}>\n".format(self.tag).encode('UTF-8'))

    def write(self, xml):
        self.f.write(tostring(xml) + b"\n")


