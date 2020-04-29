from pathlib import Path
from subprocess import check_call
from tempfile import mkdtemp
from typing import List, Union
from unittest import TestCase

from f2p.helpers import path_to_bin_ep_macro


# things to test:

# DEBUGGING
# ##list
# ##nolist
# ##show
# ##noshow
# ##showdetail
# ##noshowdetail
# ##expandcomment
# ##noexpandcomment
# ##traceback
# ##notraceback
# ##write
# ##nowrite
# ##symboltable
# ##clear
# ##reserve TEXT k NAMES l STACK m
# ##! <comment>

# nested evaluations
# nested blocks
# literals can be quoted if they have spaces or special characters
# false is zero or blank
# true is any other character
# literals are limited to 40 chars

# ERRONEOUS CONDITIONS
# Missing in.imf
# Missing include files
# Bad syntax
# Invalid operators
# Recursion fails

# LIMITING CONDITIONS?  No, we just won't have them

class TestEPMacro(TestCase):

    def setUp(self) -> None:
        self.working_directory_string = mkdtemp()
        self.working_directory = Path(self.working_directory_string)
        self.in_imf_path = self.working_directory / 'in.imf'
        self.out_idf_path = self.working_directory / 'out.idf'

    def _run_ep_macro(self):
        ep_macro_path = path_to_bin_ep_macro()
        check_call(ep_macro_path.as_posix(), cwd=self.working_directory_string)
        self.assertTrue(self.out_idf_path.exists())

    def test_ep_macro_exists(self):
        ep_macro_path = path_to_bin_ep_macro()
        self.assertTrue(ep_macro_path.exists())

    def _write_in_imf_text(self, contents: str):
        with self.in_imf_path.open('w'):
            self.in_imf_path.write_text(contents)


class TestInclusion(TestEPMacro):

    def test_basic_include(self):
        include_file_path = self.working_directory / 'include.in'
        with include_file_path.open('w'):
            include_file_path.write_text('included lines of\ntext\n')
        self._write_in_imf_text("""
LINE1
##include include.in
LINE3
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('LINE1\nincluded lines of\ntext\nLINE3', output)

    def test_basic_include_newline_added(self):
        include_file_path = self.working_directory / 'include.in'
        with include_file_path.open('w'):
            include_file_path.write_text('included lines of\ntext')
        self._write_in_imf_text("""
LINE1
##include include.in
LINE3
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('LINE1\nincluded lines of\ntext\nLINE3', output)

    def test_include_in_subdir(self):
        sub_dir = self.working_directory / 'inc'
        sub_dir.mkdir()
        include_file_path = sub_dir / 'include.in'
        with include_file_path.open('w'):
            include_file_path.write_text('included_contents')
        self._write_in_imf_text(f"""
LINE1
##fileprefix {sub_dir}/
##include include.in
LINE3
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('LINE1\nincluded_contents\nLINE3', output)
        # path can be on the filename instead...
        self._write_in_imf_text(f"""
LINE1
##fileprefix {sub_dir}
##include /include.in
LINE3
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('LINE1\nincluded_contents\nLINE3', output)

    def test_nested_include(self):
        include_file_path_1 = self.working_directory / 'include1.in'
        with include_file_path_1.open('w'):
            include_file_path_1.write_text('include_1_line_1\n##include include2.in\ninclude_1_line_2')
        include_file_path_2 = self.working_directory / 'include2.in'
        with include_file_path_2.open('w'):
            include_file_path_2.write_text('include_2_contents')
        self._write_in_imf_text("""
LINE1
##include include1.in
LINE3
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('LINE1\ninclude_1_line_1\ninclude_2_contents\ninclude_1_line_2\nLINE3', output)

    def test_silent_include_operations(self):
        include_file_path = self.working_directory / 'include.in'
        with include_file_path.open('w'):
            include_file_path.write_text('included_contents')
        self._write_in_imf_text("""
LINE1
##includesilent include.in
##nosilent
##includesilent include.in
LINE3
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        # EPMACRO BUG: I can't get includesilent to do anything different than include
        self.assertEqual('LINE1\nincluded_contents\nincluded_contents\nLINE3', output)


class TestDefines(TestEPMacro):

    def test_simple_defines(self):
        self._write_in_imf_text("""
##def1 a 1
  ##def1 b 2
##def1   c 3
##def1 d   4
##def1 e [] 5
##def1 f [ ]  6
b[]e[]f[]a[]c[]d[]
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('256134', output)

    def test_multiline_define(self):
        self._write_in_imf_text("""
##def two_lines[]
hello,
world!
##enddef
##def three_lines []
hello,
world,
again!
##enddef
three_lines[]
two_lines[]
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('hello,\nworld,\nagain!\nhello,\nworld!', output)

    def test_argument_defines(self):
        self._write_in_imf_text("""
##def function_of_x[x]
xx x xx
##enddef
##def function_of_x_y [x y]
x y y z
##enddef
##def function_of_x_y_z [x, y z]
x z y
y z x
##enddef
function_of_x_y[3, 2]
function_of_x_y[1 2]
function_of_x[ 8 ]
function_of_x_y_z[7 8, 9]
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('3 2 2 z\n1 2 2 z\nxx 8 xx\n7 9 8\n8 9 7', output)


class TestLogicBlocks(TestEPMacro):

    def test_simple_if_def_block(self):
        self._write_in_imf_text("""
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

    def test_complex_if_condition(self):
        self._write_in_imf_text("""
##def1 true_1 1
##def1 true_2 2
##def1 false_1 0
##if #[ true_1[] AND #[ true_2[] AND #[ '' NOT false_1[] ] ] ]
abc
##else
def
##endif
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('abc', output)

    def test_complex_if_condition_else(self):
        self._write_in_imf_text("""
##def1 true_1 1
##def1 not_true 0
##def1 false_1 0
##if #[ true_1[] AND #[ not_true[] AND #[ '' NOT false_1[] ] ] ]
abc
##else
def
##endif
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('def', output)

    def test_nested_if_block(self):
        self._write_in_imf_text("""
##def1 true_1 1
##def1 true_2 2
##def1 false_1 0
##if true_1[]
  ##if true_2[]
    ##if #[ '' NOT false_1[] ]
      abc
    ##else
      def
    ##endif
  ##else
    ghi
  ##endif
##else
  jkl
##endif
""")
        self._run_ep_macro()
        output = self.out_idf_path.read_text().strip()
        self.assertEqual('abc', output)


class TestEvaluations(TestEPMacro):

    def _write_in_imf_from_answer_key(self, answer_key: List[List[Union[str, float, None]]]):
        with self.in_imf_path.open('w'):
            self.in_imf_path.write_text('\n'.join([x[0] for x in answer_key]))

    def _perform_eval_assertions(self, answer_key: List[List[Union[str, float, None]]]):
        output_lines = self.out_idf_path.read_text().split('\n')
        output_line_num = -1
        for x in range(len(answer_key)):
            if answer_key[x][1] is not None:
                output_line_num += 1
                output_line = output_lines[output_line_num].strip()
                raw_output_tokens = output_line.split(',')
                trimmed_output_tokens = [x.strip() for x in raw_output_tokens]
                self.assertEqual(2, len(trimmed_output_tokens))
                if isinstance(answer_key[x][1], str):
                    self.assertEqual(answer_key[x][1], trimmed_output_tokens[0])
                    self.assertEqual(answer_key[x][1], trimmed_output_tokens[1])
                else:
                    self.assertAlmostEqual(float(answer_key[x][1]), float(trimmed_output_tokens[0]), 3)
                    self.assertAlmostEqual(float(answer_key[x][1]), float(trimmed_output_tokens[1]), 3)

    def test_math_evaluations(self):
        test_answer_key_by_line = [
            ['##def1 x_1 1', None],
            ['##def1 x_2 2', None],
            ['##def1 x_3 3', None],
            ['##def1 x_4 4', None],
            ['##def1 x_neg_1 -1', None],
            ['##def1 x_one_quarter 0.25', None],
            ['##def1 x_half 0.5', None],
            ['##def1 x_three_quarter 0.75', None],
            ['##def1 x_one_and_half 1.5', None],
            ['#eval[ x_1[] + x_2[] ],#[ x_1[] + x_2[] ]', 3],
            ['#eval[ x_1[] - x_2[] ],#[ x_1[] - x_2[] ]', -1],
            ['#eval[ x_1[] * x_2[] ],#[ x_1[] * x_2[] ]', 2],
            ['#eval[ x_1[] / x_2[] ],#[ x_1[] / x_2[] ]', 0.5],
            ['#eval[ x_1[] min x_2[] ],#[ x_1[] min x_2[] ]', 1],
            ['#eval[ x_1[] max x_2[] ],#[ x_1[] max x_2[] ]', 2],
            ['#eval[ x_4[] mod x_3[] ],#[ x_4[] mod x_3[] ]', 1],
            ['#eval[ x_4[] ** x_3[] ],#[ x_4[] ** x_3[] ]', 64],
            ['#eval[ SIN OF x_3[] ],#[ sin of x_3[] ]', 0.0523],
            ['#eval[ COS OF x_3[] ],#[ cos of x_3[] ]', 0.9986],
            ['#eval[ TAN OF x_3[] ],#[ tan of x_3[] ]', 0.0524],
            ['#eval[ SQRT OF x_3[] ],#[ sqrt of x_3[] ]', 1.7321],
            ['#eval[ ABS OF x_neg_1[] ],#[ abs of x_1[] ]', 1],
            ['#eval[ ASIN OF x_half[] ],#[ asin of x_half[] ]', 30],
            ['#eval[ ACOS OF x_half[] ],#[ acos of x_half[] ]', 60],
            ['#eval[ ATAN OF x_half[] ],#[ atan of x_half[] ]', 26.5651],
            ['#eval[ INT OF x_one_quarter[] ],#[ int of x_one_quarter[] ]', 0.0],
            ['#eval[ INT OF x_half[] ],#[ int of x_half[] ]', 0.0],
            ['#eval[ INT OF x_three_quarter[] ],#[ int of x_three_quarter[] ]', 0.0],
            # ['#eval[ INT OF x_one_and_half[] ],#[ int of x_one_and_half[] ]', 7.0],  # EPMACRO BUG: int(1.5) -> 0
            ['#eval[ LOG10 OF x_3[] ],#[ log10 of x_3[] ]', 0.4771],
            ['#eval[ LOG OF x_3[] ],#[ log of x_3[] ]', 1.0986],
        ]
        self._write_in_imf_from_answer_key(test_answer_key_by_line)
        self._run_ep_macro()
        self._perform_eval_assertions(test_answer_key_by_line)

    def test_string_evaluations(self):
        test_answer_key_by_line = [
            ['##def1 s_1 hello', None],
            ['##def1 s_2 world', None],
            ['##def1 s_3 HELLO', None],
            ['##def1 s_4 WORLD', None],
            ['#eval[ hello // world ],#[ hello // world ]', '"helloworld"'],
            ['#eval[ s_1[] // s_2[] ],#[ s_1[] // s_2[] ]', '"helloworld"'],
            ['#eval[ s_1[] // world ],#[ hello // s_2[] ]', '"helloworld"'],
            ['#eval[ s_1[] /// s_2[] ],#[ s_1[] /// s_2[] ]', '"hello world"'],
            ['#eval[ s_1[] /// world ],#[ hello /// s_2[] ]', '"hello world"'],
            ['#eval[ a EQS a ],#[ a EQS a ]', '1'],
            ['#eval[ s_1[] EQS s_1[] ],#[ s_1[] EQS s_1[] ]', '1'],
            ['#eval[ s_1[] EQS s_2[] ],#[ s_1[] EQS s_2[] ]', '0'],
            ['#eval[ a NES a ],#[ a NES a ]', '0'],
            ['#eval[ s_1[] NES s_1[] ],#[ s_1[] NES s_1[] ]', '0'],
            ['#eval[ s_1[] NES s_2[] ],#[ s_1[] NES s_2[] ]', '1'],
            ['#eval[ A EQSU a ],#[ a EQSU A ]', '1'],
            ['#eval[ s_1[] EQSU s_3[] ],#[ s_1[] EQSU s_3[] ]', '1'],
            ['#eval[ s_1[] EQSU s_4[] ],#[ s_1[] EQSU s_4[] ]', '0'],
            ['#eval[ A NESU a ],#[ A NESU a ]', '0'],
            ['#eval[ s_1[] NESU s_3[] ],#[ s_1[] NESU s_3[] ]', '0'],
            ['#eval[ s_1[] NESU s_4[] ],#[ s_1[] NESU s_4[] ]', '1'],
        ]
        self._write_in_imf_from_answer_key(test_answer_key_by_line)
        self._run_ep_macro()
        self._perform_eval_assertions(test_answer_key_by_line)

    def test_logical_evaluations(self):
        test_answer_key_by_line = [
            ['##def1 l_true #[ a EQS a ]', None],
            ['##def1 l_false #[ a NES a ]', None],
            ['#eval[ l_true[] AND l_true[] ],#[ l_true[] AND l_true[] ]', '1'],
            ['#eval[ l_true[] AND l_false[] ],#[ l_true[] AND l_false[] ]', '0'],
            ['#eval[ l_false[] AND l_true[] ],#[ l_false[] AND l_true[] ]', '0'],
            ['#eval[ l_false[] AND l_false[] ],#[ l_false[] AND l_false[] ]', '0'],
            ['#eval[ l_true[] OR l_true[] ],#[ l_true[] OR l_true[] ]', '1'],
            ['#eval[ l_true[] OR l_false[] ],#[ l_true[] OR l_false[] ]', '1'],
            ['#eval[ l_false[] OR l_true[] ],#[ l_false[] OR l_true[] ]', '1'],
            ['#eval[ l_false[] OR l_false[] ],#[ l_false[] OR l_false[] ]', '0'],
            ['#eval[ "" NOT l_true[] ],#[ "" NOT l_true[] ]', '0'],  # EPMACRO BUG: Docs show it doesn't need arg1
            ['#eval[ "" NOT l_false[] ],#[ "" NOT l_false[] ]', '1'],
            ['#eval[ 3 EQ 3 ],#[ 3 eq 3 ]', '1'],
            ['#eval[ 1 EQ 3 ],#[ 1 eq 3 ]', '0'],
            ['#eval[ 2 NE 3 ],#[ 2 ne 3 ]', '1'],
            ['#eval[ 3 NE 3 ],#[ 3 ne 3 ]', '0'],
            ['#eval[ 5 GT 3 ],#[ 5 gt 3 ]', '1'],
            ['#eval[ 5 GT 5 ],#[ 5 gt 5 ]', '0'],
            ['#eval[ 5 GE 3 ],#[ 5 ge 3 ]', '1'],
            ['#eval[ 5 GE 5 ],#[ 5 ge 5 ]', '1'],
            ['#eval[ 3 LT 5 ],#[ 3 lt 5 ]', '1'],
            ['#eval[ 5 LT 5 ],#[ 5 lt 5 ]', '0'],
            ['#eval[ 3 LE 5 ],#[ 3 le 5 ]', '1'],
            ['#eval[ 5 LE 5 ],#[ 5 le 5 ]', '1'],
        ]
        self._write_in_imf_from_answer_key(test_answer_key_by_line)
        self._run_ep_macro()
        self._perform_eval_assertions(test_answer_key_by_line)
