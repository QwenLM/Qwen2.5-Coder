package java

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/zimmski/osutil"
	"github.com/zimmski/osutil/bytesutil"

	"github.com/symflower/eval-dev-quality/language"
	languagetesting "github.com/symflower/eval-dev-quality/language/testing"
	"github.com/symflower/eval-dev-quality/log"
)

func TestLanguageFiles(t *testing.T) {
	type testCase struct {
		Name string

		Language *Language

		RepositoryPath string

		ExpectedFilePaths []string
		ExpectedError     error
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			logOutput, logger := log.Buffer()
			defer func() {
				if t.Failed() {
					t.Log(logOutput.String())
				}
			}()

			if tc.Language == nil {
				tc.Language = &Language{}
			}
			actualFilePaths, actualError := tc.Language.Files(logger, tc.RepositoryPath)

			assert.Equal(t, tc.ExpectedFilePaths, actualFilePaths)
			assert.Equal(t, tc.ExpectedError, actualError)
		})
	}

	validate(t, &testCase{
		Name: "Plain",

		RepositoryPath: filepath.Join("..", "..", "testdata", "java", "plain"),

		ExpectedFilePaths: []string{
			filepath.Join("src", "main", "java", "com", "eval", "Plain.java"),
		},
	})
}

func TestLanguageImportPath(t *testing.T) {
	type testCase struct {
		Name string

		Language *Language

		ProjectRootPath string
		FilePath        string

		ExpectedImportPath string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			if tc.Language == nil {
				tc.Language = &Language{}
			}

			actualImportPath := tc.Language.ImportPath(tc.ProjectRootPath, tc.FilePath)

			assert.Equal(t, tc.ExpectedImportPath, actualImportPath)
		})
	}

	validate(t, &testCase{
		Name: "Source file",

		FilePath: "src/main/java/com/eval/Plain.java",

		ExpectedImportPath: "com.eval",
	})
}

func TestLanguageTestFilePath(t *testing.T) {
	type testCase struct {
		Name string

		Language *Language

		ProjectRootPath string
		FilePath        string

		ExpectedTestFilePath string
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			if tc.Language == nil {
				tc.Language = &Language{}
			}

			actualTestFilePath := tc.Language.TestFilePath(tc.ProjectRootPath, tc.FilePath)

			assert.Equal(t, tc.ExpectedTestFilePath, actualTestFilePath)
		})
	}

	if osutil.IsWindows() {
		validate(t, &testCase{
			Name: "Source file",

			FilePath: "src\\main\\java\\com\\eval\\Plain.java",

			ExpectedTestFilePath: "src\\test\\java\\com\\eval\\PlainTest.java",
		})
	} else {
		validate(t, &testCase{
			Name: "Source file",

			FilePath: "src/main/java/com/eval/Plain.java",

			ExpectedTestFilePath: "src/test/java/com/eval/PlainTest.java",
		})
	}
}

func TestLanguageExecute(t *testing.T) {
	validate := func(t *testing.T, tc *languagetesting.TestCaseExecuteTests) {
		if tc.Language == nil {
			tc.Language = &Language{}
		}

		tc.Validate(t)
	}

	validate(t, &languagetesting.TestCaseExecuteTests{
		Name: "No test files",

		RepositoryPath: filepath.Join("..", "..", "testdata", "java", "plain"),

		ExpectedTestResult: &language.TestResult{
			Coverage: 0,
		},
		ExpectedErrorText: "exit status 1",
	})

	t.Run("With test file", func(t *testing.T) {
		validate(t, &languagetesting.TestCaseExecuteTests{
			Name: "Valid",

			RepositoryPath: filepath.Join("..", "..", "testdata", "java", "plain"),
			RepositoryChange: func(t *testing.T, repositoryPath string) {
				javaTestFilePath := filepath.Join(repositoryPath, "src/test/java/com/eval/PlainSymflowerTest.java")
				require.NoError(t, os.MkdirAll(filepath.Dir(javaTestFilePath), 0755))
				require.NoError(t, os.WriteFile(javaTestFilePath, []byte(bytesutil.StringTrimIndentations(`
					package com.eval;

					import org.junit.jupiter.api.*;

					public class PlainSymflowerTest {
						@Test
						public void plain1() {
							Plain.plain();
						}
					}
				`)), 0660))
			},

			ExpectedTestResult: &language.TestResult{
				TestsTotal: 1,
				TestsPass:  1,

				Coverage: 1,
			},
		})

		validate(t, &languagetesting.TestCaseExecuteTests{
			Name: "Failing tests",

			RepositoryPath: filepath.Join("..", "..", "testdata", "java", "light"),
			RepositoryChange: func(t *testing.T, repositoryPath string) {
				javaTestFilePath := filepath.Join(repositoryPath, "src/test/java/com/eval/SimpleIfElseSymflowerTest.java")
				require.NoError(t, os.MkdirAll(filepath.Dir(javaTestFilePath), 0755))
				require.NoError(t, os.WriteFile(javaTestFilePath, []byte(bytesutil.StringTrimIndentations(`
					package com.eval;

					import org.junit.jupiter.api.*;

					public class SimpleIfElseSymflowerTest {
						@Test
						public void simpleIfElse() {
							int actual = SimpleIfElse.simpleIfElse(1); // Get some coverage...
							Assertions.assertEquals(true, false); // ... and then fail.
						}
					}
				`)), 0660))
			},

			ExpectedTestResult: &language.TestResult{
				TestsTotal: 1,
				TestsPass:  0,

				Coverage: 3,
			},
		})

		validate(t, &languagetesting.TestCaseExecuteTests{
			Name: "Syntax error",

			RepositoryPath: filepath.Join("..", "..", "testdata", "java", "plain"),
			RepositoryChange: func(t *testing.T, repositoryPath string) {
				javaTestFilePath := filepath.Join(repositoryPath, "src/test/java/com/eval/PlainSymflowerTest.java")
				require.NoError(t, os.MkdirAll(filepath.Dir(javaTestFilePath), 0755))
				require.NoError(t, os.WriteFile(javaTestFilePath, []byte(bytesutil.StringTrimIndentations(`
					foobar
				`)), 0660))
			},

			ExpectedErrorText: "exit status 1",
		})
	})
}

func TestMistakes(t *testing.T) {
	type testCase struct {
		Name string

		RepositoryPath string

		ExpectedMistakes []string
	}

	validate := func(t *testing.T, tc *languagetesting.TestCaseMistakes) {
		tc.Validate(t)
	}

	validate(t, &languagetesting.TestCaseMistakes{
		Name: "Method without opening brackets",

		Language:       &Language{},
		RepositoryPath: filepath.Join("..", "..", "testdata", "java", "mistakes", "openingBracketMissing"),

		ExpectedMistakes: []string{
			filepath.Join("src", "main", "java", "com", "eval", "OpeningBracketMissing.java") + ":[12,17] illegal start of type",
			filepath.Join("src", "main", "java", "com", "eval", "OpeningBracketMissing.java") + ":[14,1] class, interface, or enum expected",
			filepath.Join("src", "main", "java", "com", "eval", "OpeningBracketMissing.java") + ":[4,55] ';' expected",
			filepath.Join("src", "main", "java", "com", "eval", "OpeningBracketMissing.java") + ":[8,17] illegal start of type",
			filepath.Join("src", "main", "java", "com", "eval", "OpeningBracketMissing.java") + ":[8,25] illegal start of type",
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
			actualMistakes := extractMistakes(tc.RawMistakes)

			assert.Equal(t, tc.ExpectedMistakes, actualMistakes)
		})
	}

	validate(t, &testCase{
		Name: "Plain",

		RawMistakes: bytesutil.StringTrimIndentations(`
			[INFO] Scanning for projects...
			[INFO]
			[INFO] ----------------------< com.symflower:playground >----------------------
			[INFO] Building playground 1.0-SNAPSHOT
			[INFO]   from pom.xml
			[INFO] --------------------------------[ jar ]---------------------------------
			[INFO]
			[INFO] --- clean:3.2.0:clean (default-clean) @ playground ---
			[INFO] Deleting /some/path/to/the/target
			[INFO]
			[INFO] --- resources:3.3.1:resources (default-resources) @ playground ---
			[WARNING] Using platform encoding (UTF-8 actually) to copy filtered resources, i.e. build is platform dependent!
			[INFO] Copying 0 resource from src/main/resources to target/classes
			[INFO]
			[INFO] --- compiler:3.11.0:compile (default-compile) @ playground ---
			[INFO] Changes detected - recompiling the module! :source
			[WARNING] File encoding has not been set, using platform encoding UTF-8, i.e. build is platform dependent!
			[INFO] Compiling 1 source file with javac [debug target 17] to target/classes
			[INFO] -------------------------------------------------------------
			[ERROR] COMPILATION ERROR :
			[INFO] -------------------------------------------------------------
			[ERROR] /src/main/java/com/eval/MethodWithoutOpeningBracket.java:[4,61] ';' expected
			[ERROR] /src/main/java/com/eval/MethodWithoutOpeningBracket.java:[7,1] class, interfaceenum, or record expected
			[INFO] 2 errors
			[INFO] -------------------------------------------------------------
			[INFO] ------------------------------------------------------------------------
			[INFO] BUILD FAILURE
			[INFO] ------------------------------------------------------------------------
			[INFO] Total time:  0.744 s
			[INFO] Finished at: 2024-06-05T11:27:43+01:00
			[INFO] ------------------------------------------------------------------------
			[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.11.0:compile (default-compile) on projecplayground: Compilation failure: Compilation failure:
			[ERROR] /src/main/java/com/eval/MethodWithoutOpeningBracket.java:[4,61] ';' expected
			[ERROR] /src/main/java/com/eval/MethodWithoutOpeningBracket.java:[7,1] class, interfaceenum, or record expected
			[ERROR] -> [Help 1]
			[ERROR]
			[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
			[ERROR] Re-run Maven using the -X switch to enable full debug logging.
			[ERROR]
			[ERROR] For more information about the errors and possible solutions, please read the following articles:
			[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException
		`),
		ExpectedMistakes: []string{
			"/src/main/java/com/eval/MethodWithoutOpeningBracket.java:[4,61] ';' expected",
			"/src/main/java/com/eval/MethodWithoutOpeningBracket.java:[7,1] class, interfaceenum, or record expected",
		},
	})
}

func TestParseSymflowerTestOutput(t *testing.T) {
	type testCase struct {
		Name string

		Data string

		ExpectedTestsTotal int
		ExpectedTestsPass  int
		ExpectedErr        error
	}

	validate := func(t *testing.T, tc *testCase) {
		t.Run(tc.Name, func(t *testing.T) {
			actualTestsTotal, actualTestsPass, actualErr := parseSymflowerTestOutput(bytesutil.StringTrimIndentations(tc.Data))

			assert.Equal(t, tc.ExpectedTestsTotal, actualTestsTotal)
			assert.Equal(t, tc.ExpectedTestsPass, actualTestsPass)
			assert.Equal(t, tc.ExpectedErr, actualErr)
		})
	}

	validate(t, &testCase{
		Name: "Passing tests only",

		Data: `
			[INFO] Scanning for projects...
			[WARNING]
			[WARNING] Some problems were encountered while building the effective model for eval.dev.quality:is-sorted:jar:SNAPSHOT
			[WARNING] 'version' uses an unsupported snapshot version format, should be '*-SNAPSHOT' instead. @ line 8, column 11
			[WARNING]
			[WARNING] It is highly recommended to fix these problems because they threaten the stability of your build.
			[WARNING]
			[WARNING] For this reason, future Maven versions might no longer support building such malformed projects.
			[WARNING]
			[INFO]
			[INFO] ---------------------< eval.dev.quality:is-sorted >---------------------
			[INFO] Building is-sorted SNAPSHOT
			[INFO]   from pom.xml
			[INFO] --------------------------------[ jar ]---------------------------------
			[INFO]
			[INFO] --- resources:3.3.0:resources (default-resources) @ is-sorted ---
			[WARNING] Using platform encoding (UTF-8 actually) to copy filtered resources, i.e. build is platform dependent!
			[INFO] skip non existing resourceDirectory /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/src/main/resources
			[INFO]
			[INFO] --- compiler:3.10.1:compile (default-compile) @ is-sorted ---
			[INFO] Changes detected - recompiling the module!
			[WARNING] File encoding has not been set, using platform encoding UTF-8, i.e. build is platform dependent!
			[INFO] Compiling 1 source file to /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/target/classes
			[INFO]
			[INFO] --- resources:3.3.0:testResources (default-testResources) @ is-sorted ---
			[WARNING] Using platform encoding (UTF-8 actually) to copy filtered resources, i.e. build is platform dependent!
			[INFO] skip non existing resourceDirectory /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/src/test/resources
			[INFO]
			[INFO] --- compiler:3.10.1:testCompile (default-testCompile) @ is-sorted ---
			[INFO] Changes detected - recompiling the module!
			[WARNING] File encoding has not been set, using platform encoding UTF-8, i.e. build is platform dependent!
			[INFO] Compiling 1 source file to /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/target/test-classes
			[INFO]
			[INFO] --- surefire:3.2.5:test (default-test) @ is-sorted ---
			[INFO] Using auto detected provider org.apache.maven.surefire.junitplatform.JUnitPlatformProvider
			[INFO]
			[INFO] -------------------------------------------------------
			[INFO]  T E S T S
			[INFO] -------------------------------------------------------
			[INFO] Running com.eval.IsSortedTest
			[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.295 s -- in com.eval.IsSortedTest
			[INFO]
			[INFO] Results:
			[INFO]
			[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
			[INFO]
			[INFO] ------------------------------------------------------------------------
			[INFO] BUILD SUCCESS
			[INFO] ------------------------------------------------------------------------
			[INFO] Total time:  12.959 s
			[INFO] Finished at: 2024-07-17T07:17:52+02:00
			[INFO] ------------------------------------------------------------------------
		`,

		ExpectedTestsTotal: 5,
		ExpectedTestsPass:  5,
	})
	validate(t, &testCase{
		Name: "Failing tests",

		Data: `
			[INFO] Scanning for projects...
			[WARNING]
			[WARNING] Some problems were encountered while building the effective model for eval.dev.quality:is-sorted:jar:SNAPSHOT
			[WARNING] 'version' uses an unsupported snapshot version format, should be '*-SNAPSHOT' instead. @ line 8, column 11
			[WARNING]
			[WARNING] It is highly recommended to fix these problems because they threaten the stability of your build.
			[WARNING]
			[WARNING] For this reason, future Maven versions might no longer support building such malformed projects.
			[WARNING]
			[INFO]
			[INFO] ---------------------< eval.dev.quality:is-sorted >---------------------
			[INFO] Building is-sorted SNAPSHOT
			[INFO]   from pom.xml
			[INFO] --------------------------------[ jar ]---------------------------------
			[INFO]
			[INFO] --- resources:3.3.0:resources (default-resources) @ is-sorted ---
			[WARNING] Using platform encoding (UTF-8 actually) to copy filtered resources, i.e. build is platform dependent!
			[INFO] skip non existing resourceDirectory /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/src/main/resources
			[INFO]
			[INFO] --- compiler:3.10.1:compile (default-compile) @ is-sorted ---
			[INFO] Nothing to compile - all classes are up to date
			[INFO]
			[INFO] --- resources:3.3.0:testResources (default-testResources) @ is-sorted ---
			[WARNING] Using platform encoding (UTF-8 actually) to copy filtered resources, i.e. build is platform dependent!
			[INFO] skip non existing resourceDirectory /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/src/test/resources
			[INFO]
			[INFO] --- compiler:3.10.1:testCompile (default-testCompile) @ is-sorted ---
			[INFO] Nothing to compile - all classes are up to date
			[INFO]
			[INFO] --- surefire:3.2.5:test (default-test) @ is-sorted ---
			[INFO] Using auto detected provider org.apache.maven.surefire.junitplatform.JUnitPlatformProvider
			[INFO]
			[INFO] -------------------------------------------------------
			[INFO]  T E S T S
			[INFO] -------------------------------------------------------
			[INFO] Running com.eval.IsSortedTest
			[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.081 s <<< FAILURE! -- in com.eval.IsSortedTest
			[ERROR] com.eval.IsSortedTest.isSorted4 -- Time elapsed: 0.006 s <<< FAILURE!
			org.opentest4j.AssertionFailedError: expected: <false> but was: <true>
					at org.junit.jupiter.api.AssertionUtils.fail(AssertionUtils.java:55)
					at org.junit.jupiter.api.AssertFalse.assertFalse(AssertFalse.java:40)
					at org.junit.jupiter.api.AssertFalse.assertFalse(AssertFalse.java:35)
					at org.junit.jupiter.api.Assertions.assertFalse(Assertions.java:227)
					at com.eval.IsSortedTest.isSorted4(IsSortedTest.java:38)
					at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
					at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
					at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
					at java.base/java.lang.reflect.Method.invoke(Method.java:566)
					at org.junit.platform.commons.util.ReflectionUtils.invokeMethod(ReflectionUtils.java:725)
					at org.junit.jupiter.engine.execution.MethodInvocation.proceed(MethodInvocation.java:60)
					at org.junit.jupiter.engine.execution.InvocationInterceptorChain$ValidatingInvocation.proceed(InvocationInterceptorChain.java:131)
					at org.junit.jupiter.engine.extension.TimeoutExtension.intercept(TimeoutExtension.java:149)
					at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestableMethod(TimeoutExtension.java:140)
					at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestMethod(TimeoutExtension.java:84)
					at org.junit.jupiter.engine.execution.ExecutableInvoker$ReflectiveInterceptorCall.lambda$ofVoidMethod$0(ExecutableInvoker.java:115)
					at org.junit.jupiter.engine.execution.ExecutableInvoker.lambda$invoke$0(ExecutableInvoker.java:105)
					at org.junit.jupiter.engine.execution.InvocationInterceptorChain$InterceptedInvocation.proceed(InvocationInterceptorChain.java:106)
					at org.junit.jupiter.engine.execution.InvocationInterceptorChain.proceed(InvocationInterceptorChain.java:64)
					at org.junit.jupiter.engine.execution.InvocationInterceptorChain.chainAndInvoke(InvocationInterceptorChain.java:45)
					at org.junit.jupiter.engine.execution.InvocationInterceptorChain.invoke(InvocationInterceptorChain.java:37)
					at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:104)
					at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:98)
					at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.lambda$invokeTestMethod$7(TestMethodTestDescriptor.java:214)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.invokeTestMethod(TestMethodTestDescriptor.java:210)
					at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:135)
					at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:66)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:151)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
					at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
					at java.base/java.util.ArrayList.forEach(ArrayList.java:1541)
					at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
					at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
					at java.base/java.util.ArrayList.forEach(ArrayList.java:1541)
					at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
					at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
					at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
					at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
					at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.submit(SameThreadHierarchicalTestExecutorService.java:35)
					at org.junit.platform.engine.support.hierarchical.HierarchicalTestExecutor.execute(HierarchicalTestExecutor.java:57)
					at org.junit.platform.engine.support.hierarchical.HierarchicalTestEngine.execute(HierarchicalTestEngine.java:54)
					at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:107)
					at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:88)
					at org.junit.platform.launcher.core.EngineExecutionOrchestrator.lambda$execute$0(EngineExecutionOrchestrator.java:54)
					at org.junit.platform.launcher.core.EngineExecutionOrchestrator.withInterceptedStreams(EngineExecutionOrchestrator.java:67)
					at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:52)
					at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:114)
					at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:86)
					at org.junit.platform.launcher.core.DefaultLauncherSession$DelegatingLauncher.execute(DefaultLauncherSession.java:86)
					at org.apache.maven.surefire.junitplatform.LazyLauncher.execute(LazyLauncher.java:56)
					at org.apache.maven.surefire.junitplatform.JUnitPlatformProvider.execute(JUnitPlatformProvider.java:184)
					at org.apache.maven.surefire.junitplatform.JUnitPlatformProvider.invokeAllTests(JUnitPlatformProvider.java:148)
					at org.apache.maven.surefire.junitplatform.JUnitPlatformProvider.invoke(JUnitPlatformProvider.java:122)
					at org.apache.maven.surefire.booter.ForkedBooter.runSuitesInProcess(ForkedBooter.java:385)
					at org.apache.maven.surefire.booter.ForkedBooter.execute(ForkedBooter.java:162)
					at org.apache.maven.surefire.booter.ForkedBooter.run(ForkedBooter.java:507)
					at org.apache.maven.surefire.booter.ForkedBooter.main(ForkedBooter.java:495)

			[INFO]
			[INFO] Results:
			[INFO]
			[ERROR] Failures:
			[ERROR]   IsSortedTest.isSorted4:38 expected: <false> but was: <true>
			[INFO]
			[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0
			[INFO]
			[INFO] ------------------------------------------------------------------------
			[INFO] BUILD FAILURE
			[INFO] ------------------------------------------------------------------------
			[INFO] Total time:  1.652 s
			[INFO] Finished at: 2024-07-17T07:19:39+02:00
			[INFO] ------------------------------------------------------------------------
			[ERROR] Failed to execute goal org.apache.maven.plugins:maven-surefire-plugin:3.2.5:test (default-test) on project is-sorted: There are test failures.
			[ERROR]
			[ERROR] Please refer to /home/andreas/repos/eval-dev-quality/testdata/java/transpile/isSorted/target/surefire-reports for the individual test results.
			[ERROR] Please refer to dump files (if any exist) [date].dump, [date]-jvmRun[N].dump and [date].dumpstream.
			[ERROR] -> [Help 1]
			[ERROR]
			[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
			[ERROR] Re-run Maven using the -X switch to enable full debug logging.
			[ERROR]
			[ERROR] For more information about the errors and possible solutions, please read the following articles:
			[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException
		`,

		ExpectedTestsTotal: 5,
		ExpectedTestsPass:  4,
	})
}
