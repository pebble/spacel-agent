import unittest

from spacel.aws.helpers import read_file


class TestAwsHelpers(unittest.TestCase):
    def test_read_file(self):
        output = read_file('test/open.test', 'default')
        self.assertEquals('test', output)

    def test_read_file_error(self):
        output = read_file('test/file/does/not/exist', 'default')
        self.assertEquals('default', output)
