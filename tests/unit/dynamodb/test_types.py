#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
from decimal import Decimal
from tests.compat import unittest

from boto.compat import six
from boto.dynamodb import types
from boto.dynamodb.exceptions import DynamoDBNumberError


class TestDynamizer(unittest.TestCase):
    def setUp(self):
        pass

    def test_encoding_to_dynamodb(self):
        dynamizer = types.Dynamizer()
        self.assertEqual(dynamizer.encode('foo'), {'S': 'foo'})
        self.assertEqual(dynamizer.encode(54), {'N': '54'})
        self.assertEqual(dynamizer.encode(Decimal('1.1')), {'N': '1.1'})
        self.assertEqual(dynamizer.encode(set([1, 2, 3])),
                         {'NS': ['1', '2', '3']})
        self.assertIn(dynamizer.encode(set(['foo', 'bar'])),
                      ({'SS': ['foo', 'bar']}, {'SS': ['bar', 'foo']}))
        self.assertEqual(dynamizer.encode(types.Binary(b'\x01')),
                         {'B': 'AQ=='})
        self.assertEqual(dynamizer.encode(set([types.Binary(b'\x01')])),
                         {'BS': ['AQ==']})

    def test_decoding_to_dynamodb(self):
        dynamizer = types.Dynamizer()
        self.assertEqual(dynamizer.decode({'S': 'foo'}), 'foo')
        self.assertEqual(dynamizer.decode({'N': '54'}), 54)
        self.assertEqual(dynamizer.decode({'N': '1.1'}), Decimal('1.1'))
        self.assertEqual(dynamizer.decode({'NS': ['1', '2', '3']}),
                         set([1, 2, 3]))
        self.assertEqual(dynamizer.decode({'SS': ['foo', 'bar']}),
                         set(['foo', 'bar']))
        self.assertEqual(dynamizer.decode({'B': 'AQ=='}), types.Binary(b'\x01'))
        self.assertEqual(dynamizer.decode({'BS': ['AQ==']}),
                         set([types.Binary(b'\x01')]))

    def test_float_conversion_errors(self):
        dynamizer = types.Dynamizer()
        # When supporting decimals, certain floats will work:
        self.assertEqual(dynamizer.encode(1.25), {'N': '1.25'})
        # And some will generate errors, which is why it's best
        # to just use Decimals directly:
        with self.assertRaises(DynamoDBNumberError):
            dynamizer.encode(1.1)

    def test_lossy_float_conversions(self):
        dynamizer = types.LossyFloatDynamizer()
        # Just testing the differences here, specifically float conversions:
        self.assertEqual(dynamizer.encode(1.1), {'N': '1.1'})
        self.assertEqual(dynamizer.decode({'N': '1.1'}), 1.1)

        self.assertEqual(dynamizer.encode(set([1.1])),
                         {'NS': ['1.1']})
        self.assertEqual(dynamizer.decode({'NS': ['1.1', '2.2', '3.3']}),
                         set([1.1, 2.2, 3.3]))


class TestBinary(unittest.TestCase):
    def test_good_input(self):
        data = types.Binary(b'\x01')
        self.assertEqual(b'\x01', data)
        self.assertEqual(b'\x01', bytes(data))

    @unittest.skipUnless(six.PY2, "Python 2 only")
    def test_bad_input(self):
        with self.assertRaises(TypeError):
            types.Binary(1)

    @unittest.skipUnless(six.PY3, "Python 3 only")
    def test_bytes_input(self):
        data = types.Binary(1)
        self.assertEqual(data, b'\x00')
        self.assertEqual(data.value, b'\x00')

    @unittest.skipUnless(six.PY2, "Python 2 only")
    def test_unicode_py2(self):
        # It's dirty. But remains for backward compatibility.
        data = types.Binary(u'\x01')
        self.assertEqual(data, b'\x01')
        self.assertEqual(bytes(data), b'\x01')

        # Delegate to built-in b'\x01' == u'\x01'
        # In Python 2.x these are considered equal
        self.assertEqual(data, u'\x01')

    @unittest.skipUnless(six.PY3, "Python 3 only")
    def test_unicode_py3(self):
        with self.assertRaises(TypeError):
            types.Binary(u'\x01')

if __name__ == '__main__':
    unittest.main()
