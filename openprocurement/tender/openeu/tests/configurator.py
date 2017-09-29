import unittest
from openprocurement.tender.core.tests.configurator import ConfiguratorTestMixin
from openprocurement.tender.openeu.adapters import TenderAboveThresholdEUConfigurator


class ConfiguratorTest(unittest.TestCase, ConfiguratorTestMixin):
    configurator_class = TenderAboveThresholdEUConfigurator
    reverse_awarding_criteria = False
    awarding_criteria_key = 'not yet implemented'


def suite():
    current_suite = unittest.TestSuite()
    current_suite.addTest(unittest.makeSuite(ConfiguratorTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')