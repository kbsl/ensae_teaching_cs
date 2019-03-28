# -*- coding: utf-8 -*-
"""
@brief      test log(time=9s)
"""
import os
import unittest
from pyquickhelper.loghelper import fLOG
from pyquickhelper.ipythonhelper import test_notebook_execution_coverage
from pyquickhelper.pycode import add_missing_development_version, ExtTestCase
import ensae_teaching_cs


class TestNotebookCov_bayesian(ExtTestCase):

    def setUp(self):
        add_missing_development_version(["pymyinstall", "pyensae", "jyquickhelper"],
                                        __file__, hide=True)

    def test_notebook_bayes(self):
        fLOG(
            __file__,
            self._testMethodName,
            OutputPrint=__name__ == "__main__")

        self.assertTrue(ensae_teaching_cs is not None)
        folder = os.path.join(os.path.dirname(__file__),
                              "..", "..", "_doc", "notebooks", "2a")
        test_notebook_execution_coverage(__file__, "bayes", folder,
                                         this_module_name="ensae_teaching_cs", fLOG=fLOG)


if __name__ == "__main__":
    unittest.main()
