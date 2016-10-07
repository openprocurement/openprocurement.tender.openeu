# -*- coding: utf-8 -*-

import unittest
from openprocurement.tender.openeu.tests import tender, dry_run


def suite():
    suite = unittest.TestSuite()
    suite.addTest(tender.suite())
    suite.addTest(dry_run.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
