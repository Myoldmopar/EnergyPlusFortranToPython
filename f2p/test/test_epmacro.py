from pathlib import Path
from subprocess import check_call
from tempfile import mkdtemp
from unittest import TestCase

from f2p.helpers import path_to_bin_ep_macro


# things to test:
# ##include {includefilename}
# ##fileprefix {prefixpathname}
# ##includesilent {includefilename}
# ##nosilent
# ##if {condition1} ...
# ##elseif {condition2} ...
# ##elseif {condition3} ...
# ##else ...
# ##endif

class TestEPMacro(TestCase):

    def setUp(self) -> None:
        self.working_directory_string = mkdtemp()
        self.working_directory = Path(self.working_directory_string)
        self.in_imf_path = self.working_directory / 'in.imf'
        self.out_idf_path = self.working_directory / 'out.idf'

    def _run_ep_macro(self):
        ep_macro_path = path_to_bin_ep_macro()
        check_call(ep_macro_path.as_posix(), cwd=self.working_directory_string)

    def test_ep_macro_exists(self):
        ep_macro_path = path_to_bin_ep_macro()
        self.assertTrue(ep_macro_path.exists())

    def test_simple_if_def_block(self):
        with self.in_imf_path.open('w'):
            self.in_imf_path.write_text("""
##def1 variable_x 1
##ifdef variable_x
abc
##else
def
##endif        
            """)
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('abc', output)

    def test_c(self):
        self.assertEqual(0, 0)

    def test_d(self):
        self.assertEqual(0, 0)
