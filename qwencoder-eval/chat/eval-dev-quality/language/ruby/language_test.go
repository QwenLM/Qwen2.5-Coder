package ruby

import (
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	languagetesting "github.com/symflower/eval-dev-quality/language/testing"
)

func TestLanguageTestFilePath(t *testing.T) {
	type testCase struct {
		Name string

		ProjectRootPath string
		FilePath        string

		ExpectedTestFilePath string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			ruby := Language{}
			actualTestFilePath := ruby.TestFilePath(tc.ProjectRootPath, tc.FilePath)

			assert.Equal(t, tc.ExpectedTestFilePath, actualTestFilePath)
		})
	}

	validate(t, &testCase{
		Name: "Source file",

		FilePath: filepath.Join("testdata", "ruby", "plain", "lib", "plain.rb"),

		ExpectedTestFilePath: filepath.Join("testdata", "ruby", "plain", "test", "plain_test.rb"),
	})
}

func TestLanguageImportPath(t *testing.T) {
	type testCase struct {
		Name string

		ProjectRootPath string
		FilePath        string

		ExpectedImportPath string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			ruby := Language{}
			actualImportPath := ruby.ImportPath(tc.ProjectRootPath, tc.FilePath)

			assert.Equal(t, tc.ExpectedImportPath, actualImportPath)
		})
	}

	validate(t, &testCase{
		Name: "Source file",

		FilePath: filepath.Join("testdata", "ruby", "plain", "lib", "plain.rb"),

		ExpectedImportPath: "../lib/plain",
	})
}

func TestParseSymflowerTestOutput(t *testing.T) {
	type testCase struct {
		Name string

		Data string

		ExpectedTestsTotal int
		ExpectedTestsPass  int
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualTestsTotal, actualTestsPass, actualErr := parseSymflowerTestOutput(bytesutil.StringTrimIndentations(tc.Data))
			require.NoError(t, actualErr)

			assert.Equal(t, tc.ExpectedTestsTotal, actualTestsTotal)
			assert.Equal(t, tc.ExpectedTestsPass, actualTestsPass)
		})
	}

	validate(t, &testCase{
		Name: "Tests with failures",

		Data: `
			Bundle complete! 3 Gemfile dependencies, 7 gems now installed.
			Bundled gems are installed into ` + "`" + `./vendor/bundle` + "`" + `
			Run options: --seed 64090

			# Running:

			F.E...

			Finished in 0.001245s, 4820.4968 runs/s, 4017.0806 assertions/s.

  			1) Failure:
			TestBalancedBrackets#test_has_balanced_brackets6 [test/balanced_brackets_test.rb:38]:
			Expected: true
  			Actual: false

  			2) Error:
			TestBalancedBrackets#test_has_balanced_brackets5:
			NoMethodError: undefined method ` + "`" + `has_balancedbrackets' for an instance of TestBalancedBrackets
    			test/balanced_brackets_test.rb:31:in ` + "`" + `test_has_balanced_brackets5'

			6 runs, 5 assertions, 1 failures, 1 errors, 0 skips
			rake aborted!
			Command failed with status (1)
		`,
		ExpectedTestsTotal: 6,
		ExpectedTestsPass:  4,
	})
	validate(t, &testCase{
		Name: "All tests pass",

		Data: `
			Bundle complete! 3 Gemfile dependencies, 7 gems now installed.
			Bundled gems are installed into ` + "`" + `./vendor/bundle` + "`" + `
			Run options: --seed 34577

			# Running:

			......

			Finished in 0.001230s, 4879.7904 runs/s, 4879.7904 assertions/s.

			6 runs, 6 assertions, 0 failures, 0 errors, 0 skips
		`,
		ExpectedTestsTotal: 6,
		ExpectedTestsPass:  6,
	})
}

func TestMistakes(t *testing.T) {
	if osutil.IsWindows() {
		t.Skip("Ruby is not tested in the Windows CI")
	}

	validate := func(t *testing.T, tc *languagetesting.TestCaseMistakes) {
		tc.Validate(t)
	}

	validate(t, &languagetesting.TestCaseMistakes{
		Name: "Argument is missing",

		Language:       &Language{},
		RepositoryPath: filepath.Join("..", "..", "testdata", "ruby", "mistakes", "argumentMissing"),

		ExpectedMistakesContains: func(t *testing.T, mistakes []string) {
			assert.Contains(t, mistakes[0], "ArgumentError: wrong number of arguments (given 1, expected 0)")
			assert.Contains(t, mistakes[0], "argument_missing.rb:1:in `argument_missing'")
		},
	})
}

func TestExtractMistakes(t *testing.T) {
	type testCase struct {
		Name string

		RawMistakes string

		ExpectedMistakes []string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualMistakes := extractMistakes(bytesutil.StringTrimIndentations(tc.RawMistakes))

			assert.Equal(t, tc.ExpectedMistakes, actualMistakes)
		})
	}

	validate(t, &testCase{
		Name: "Argument missing",

		RawMistakes: `
			Run options: --seed 51400
			# Running:
			EEE
			Finished in 0.002350s, 1276.5192 runs/s, 0.0000 assertions/s.
			1) Error:
			TestArgumentMissing#test_argument_missing2:
			ArgumentError: wrong number of arguments (given 1, expected 0)
				/home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/lib/argument_missing.rb:1:in ` + "`" + `argument_missing'
				/home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/test/argument_missing_test.rb:15:in ` + "`" + `test_argument_missing2'
			2) Error:
			TestArgumentMissing#test_argument_missing1:
			ArgumentError: wrong number of arguments (given 1, expected 0)
				/home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/lib/argument_missing.rb:1:in ` + "`" + `argument_missing'
				/home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/test/argument_missing_test.rb:8:in ` + "`" + `test_argument_missing1'
			3) Error:
			TestArgumentMissing#test_argument_missing3:
			ArgumentError: wrong number of arguments (given 1, expected 0)
				/home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/lib/argument_missing.rb:1:in ` + "`" + `argument_missing'
				/home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/test/argument_missing_test.rb:22:in ` + "`" + `test_argument_missing3'
			3 runs, 0 assertions, 0 failures, 3 errors, 0 skips
			rake aborted!
			Command failed with status (1)
			Tasks: TOP => test
			(See full trace by running task with --trace)
		`,

		ExpectedMistakes: []string{
			"ArgumentError: wrong number of arguments (given 1, expected 0) : /home/user/eval-dev-quality/testdata/ruby/mistakes/argumentMissing/lib/argument_missing.rb:1:in `argument_missing'",
		},
	})
	validate(t, &testCase{
		Name: "End keyword missing",

		RawMistakes: `
			Unmatched keyword, missing ` + "`" + `end' ?
			  1  def end_keyword_missing(x)
			> 5      if x < 0
			  7     end
			/home/user/eval-dev-quality/testdata/ruby/mistakes/endKeywordMissing/lib/end_keyword_missing.rb:9: syntax error, unexpected end-of-input, expecting ` + "`" + `end' or dummy end (SyntaxError)
			        return 0
			                ^
			        from /home/user/eval-dev-quality/testdata/ruby/mistakes/endKeywordMissing/test/end_keyword_missing_test.rb:2:in ` + "`" + `<top (required)>'
			        from <internal:/home/user/symflower/.devenv/ruby@3.3.4/ruby/lib64/ruby/3.3.0/rubygems/core_ext/kernel_require.rb>:136:in ` + "`" + `require'
			        from <internal:/home/user/symflower/.devenv/ruby@3.3.4/ruby/lib64/ruby/3.3.0/rubygems/core_ext/kernel_require.rb>:136:in ` + "`" + `require'
			        from /home/user/symflower/.devenv/ruby@3.3.4/ruby/lib64/ruby/gems/3.3.0/gems/rake-13.1.0/lib/rake/rake_test_loader.rb:21:in ` + "`" + `block in <main>'
			        from /home/user/symflower/.devenv/ruby@3.3.4/ruby/lib64/ruby/gems/3.3.0/gems/rake-13.1.0/lib/rake/rake_test_loader.rb:6:in ` + "`" + `select'
			        from /home/user/symflower/.devenv/ruby@3.3.4/ruby/lib64/ruby/gems/3.3.0/gems/rake-13.1.0/lib/rake/rake_test_loader.rb:6:in ` + "`" + `<main>'
			rake aborted!
			Command failed with status (1)
			Tasks: TOP => test
			(See full trace by running task with --trace)
		`,

		ExpectedMistakes: []string{
			"/home/user/eval-dev-quality/testdata/ruby/mistakes/endKeywordMissing/lib/end_keyword_missing.rb:9: syntax error, unexpected end-of-input, expecting `end' or dummy end (SyntaxError)",
		},
	})
	validate(t, &testCase{
		Name: "Import missing",

		RawMistakes: `
			Run options: --seed 49524
			# Running:
			EEEEEE
			Finished in 0.002865s, 2094.2218 runs/s, 0.0000 assertions/s.
			  1) Error:
			TestImportMissing#test_json_with_nested_objects:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:26:in ` + "`" + `test_json_with_nested_objects'
			  2) Error:
			TestImportMissing#test_empty_json:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:14:in ` + "`" + `test_empty_json'
			  3) Error:
			TestImportMissing#test_invalid_json:
			NameError: uninitialized constant TestImportMissing::JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:31:in ` + "`" + `test_invalid_json'
			  4) Error:
			TestImportMissing#test_valid_json:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:8:in ` + "`" + `test_valid_json'
			  5) Error:
			TestImportMissing#test_json_with_array:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:37:in ` + "`" + `test_json_with_array'
			  6) Error:
			TestImportMissing#test_json_with_numbers:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:20:in ` + "`" + `test_json_with_numbers'
			6 runs, 0 assertions, 0 failures, 6 errors, 0 skips
			rake aborted!
			Command failed with status (1)
			Tasks: TOP => test
			(See full trace by running task with --trace)
		`,

		ExpectedMistakes: []string{
			"NameError: uninitialized constant JSON : /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in `parse_json'",
		},
	})
	validate(t, &testCase{
		Name: "Import missing with a test case error first",

		RawMistakes: `
			Run options: --seed 49524
			# Running:
			EEEEEE
			Finished in 0.002865s, 2094.2218 runs/s, 0.0000 assertions/s.
			  1) Error:
			TestImportMissing#test_invalid_json:
			NameError: uninitialized constant TestImportMissing::JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:31:in ` + "`" + `test_invalid_json'
			  2) Error:
			TestImportMissing#test_json_with_nested_objects:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:26:in ` + "`" + `test_json_with_nested_objects'
			  3) Error:
			TestImportMissing#test_empty_json:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:14:in ` + "`" + `test_empty_json'
			  4) Error:
			TestImportMissing#test_valid_json:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:8:in ` + "`" + `test_valid_json'
			  5) Error:
			TestImportMissing#test_json_with_array:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:37:in ` + "`" + `test_json_with_array'
			  6) Error:
			TestImportMissing#test_json_with_numbers:
			NameError: uninitialized constant JSON
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in ` + "`" + `parse_json'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/test/import_missing_test.rb:20:in ` + "`" + `test_json_with_numbers'
			6 runs, 0 assertions, 0 failures, 6 errors, 0 skips
			rake aborted!
			Command failed with status (1)
			Tasks: TOP => test
			(See full trace by running task with --trace)
		`,

		ExpectedMistakes: []string{
			"NameError: uninitialized constant JSON : /home/user/eval-dev-quality/testdata/ruby/mistakes/importMissing/lib/import_missing.rb:2:in `parse_json'",
		},
	})
	validate(t, &testCase{
		Name: "Type unknown",

		RawMistakes: `
			Run options: --seed 38572
			# Running:
			EEE
			Finished in 0.003430s, 874.7024 runs/s, 0.0000 assertions/s.
			  1) Error:
			TestTypeUnknown#test_type_unknown2:
			NameError: uninitialized constant Intt
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/lib/type_unknown.rb:2:in ` + "`" + `type_unknown'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/test/type_unknown_test.rb:15:in ` + "`" + `test_type_unknown2'
			  2) Error:
			TestTypeUnknown#test_type_unknown1:
			NameError: uninitialized constant Intt
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/lib/type_unknown.rb:2:in ` + "`" + `type_unknown'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/test/type_unknown_test.rb:8:in ` + "`" + `test_type_unknown1'
			  3) Error:
			TestTypeUnknown#test_type_unknown3:
			NameError: uninitialized constant Intt
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/lib/type_unknown.rb:2:in ` + "`" + `type_unknown'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/test/type_unknown_test.rb:22:in ` + "`" + `test_type_unknown3'
			3 runs, 0 assertions, 0 failures, 3 errors, 0 skips
			rake aborted!
			Command failed with status (1)
			Tasks: TOP => test
			(See full trace by running task with --trace)
		`,
		ExpectedMistakes: []string{
			"NameError: uninitialized constant Intt : /home/user/eval-dev-quality/testdata/ruby/mistakes/typeUnknown/lib/type_unknown.rb:2:in `type_unknown'",
		},
	})
	validate(t, &testCase{
		Name: "Variable unknown",

		RawMistakes: `
			Run options: --seed 47783
			# Running:
			EEE
			Finished in 0.002509s, 1195.5106 runs/s, 0.0000 assertions/s.
			  1) Error:
			TestVariableUnknown#test_variable_unknown3:
			NameError: undefined local variable or method ` + "`" + `y' for an instance of TestVariableUnknown
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/lib/variable_unknown.rb:2:in ` + "`" + `variable_unknown'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/test/variable_unknown_test.rb:22:in ` + "`" + `test_variable_unknown3'
			  2) Error:
			TestVariableUnknown#test_variable_unknown2:
			NameError: undefined local variable or method ` + "`" + `y' for an instance of TestVariableUnknown
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/lib/variable_unknown.rb:2:in ` + "`" + `variable_unknown'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/test/variable_unknown_test.rb:15:in ` + "`" + `test_variable_unknown2'
			  3) Error:
			TestVariableUnknown#test_variable_unknown1:
			NameError: undefined local variable or method ` + "`" + `y' for an instance of TestVariableUnknown
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/lib/variable_unknown.rb:2:in ` + "`" + `variable_unknown'
			    /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/test/variable_unknown_test.rb:8:in ` + "`" + `test_variable_unknown1'
			3 runs, 0 assertions, 0 failures, 3 errors, 0 skips
			rake aborted!
			Command failed with status (1)
			Tasks: TOP => test
			(See full trace by running task with --trace)
		`,
		ExpectedMistakes: []string{
			"NameError: undefined local variable or method `y' for an instance of TestVariableUnknown : /home/user/eval-dev-quality/testdata/ruby/mistakes/variableUnknown/lib/variable_unknown.rb:2:in `variable_unknown'",
		},
	})
}
