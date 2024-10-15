import contextlib
import signal
# import subprocess
import json
import os
import time
import filecmp
import traceback
import shutil 
from bs4 import BeautifulSoup

# from .safe_subprocess import run
import safe_subprocess as subprocess
timeout = 15

@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

class TimeoutException(Exception):
    pass

def excute(language_type, path, task_id, temp_dir)->bool:
    if language_type == "Common Lisp":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ["sbcl", "--script", path])
                # print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return True
    elif language_type == "Emacs Lisp":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ["emacs28", "--batch", "-l", path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Elixir":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ["elixir", path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Racket" or language_type == "Scheme":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['racket', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    if 'FAILURE' not in run_result.stderr:
                        print("pass")
                        return True
                    else:
                        print("Script failed with exit code")
                        # print("Error output:", run_result.stderr)
                        return False
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Haskell":
        try:
            with time_limit(timeout):
                compile_process = subprocess.run(['ghc', path])
                # print(compile_process)
                print(compile_process.stderr)
                if compile_process.exit_code != 0:
                    print(f"Compilation failed. Return code: {compile_process.exit_code}")
                    return False
                else:
                    try:
                        # Execute compiled Haskell program
                        executable_name = path.rstrip('.hs')
                        run_process = subprocess.run([executable_name])
                    except:
                        return False
                    if run_process.exit_code != 0 or 'fail' in  run_process.stdout.lower():
                        print(f"Execution failed. Return code: {run_process.stdout}")
                        return False
                    else:
                        print("Program executed successfully.")
                        return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Shell":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['bash', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return True
    elif language_type == "PowerShell":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['pwsh', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Swift":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['swift', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stdout)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type == "Perl":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(['perl', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Tcl":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['tclsh', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Visual Basic":
        try:
            project_path = path[:-11]
            print(project_path)
            with time_limit(timeout):
                run_result = subprocess.run(
                    ["dotnet", "run", "--project", project_path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "F#":
        try:
            project_path = path[:-11]
            print(project_path)
            with time_limit(timeout):
                run_result = subprocess.run(
                    ["dotnet", "run", "--project", project_path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    # print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "JSON":
        def read_json_file(file_path):
            """读取并解析 JSON 文件."""
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return None

        def compare_json_files(file1, file2):
            """比较两个 JSON 文件是否相同."""
            json1 = read_json_file(file1)
            json2 = read_json_file(file2)

            if json1 is None or json2 is None:
                return False

            return json1 == json2

        try:
            with time_limit(timeout):
                file_path1 = path
                if '-' in task_id:
                    file_path2 = os.path.join(temp_dir,'JSON/'+ task_id.split('/')[1].split('-')[0]+'.json')
                else:
                    file_path2 = os.path.join(temp_dir,'JSON/'+ task_id.split('/')[1]+'.json')
                if compare_json_files(file_path1, file_path2):
                    print("pass")
                    return True
                else:
                    print("error")
                    return False
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "HTML":
        def read_html_file(file_path):
            """读取并解析 HTML 文件."""
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return BeautifulSoup(file, 'html.parser')
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return None

        def compare_html_files(file1, file2):
            """比较两个 HTML 文件是否相同."""
            html1 = read_html_file(file1)
            html2 = read_html_file(file2)

            if html1 is None or html2 is None:
                return False

            # 使用prettify()方法将解析后的HTML转换为字符串，然后比较字符串
            return html1.prettify().strip() == html2.prettify().strip()

        try:
            # print(path)
            with time_limit(timeout):
                file_path1 = path
                if '-' in task_id:
                    file_path2 = os.path.join(temp_dir,'HTML/'+ task_id.split('/')[1].split('-')[0] +'.html')
                else:
                    file_path2 = os.path.join(temp_dir,'HTML/'+ task_id.split('/')[1]+'.html')

                
                if compare_html_files(file_path1, file_path2):
                    print("pass")
                    return True
                else:
                    print("error")
                    return False
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "Markdown":
        def compare_markdown_files(file1, file2):
            """比较两个 Markdown 文件是否相同."""
            try:
                # 使用 filecmp 模块比较文件内容
                return filecmp.cmp(file1, file2, shallow=False)
            except FileNotFoundError as e:
                print(f"Error reading {file1} or {file2}: {e}")
                return False

        # 使用示例
        try:
            # print(path)
            with time_limit(timeout):
                file_path1 = path
                if '-' in task_id:
                    file_path2 = os.path.join(temp_dir,'Markdown/' + task_id.split('/')[1].split('-')[0] + '.md')
                else:
                    file_path2 = os.path.join(temp_dir,'Markdown/' + task_id.split('/')[1] + '.md')
                if compare_markdown_files(file_path1, file_path2):
                    print("pass")
                    return True
                else:
                    print("error")
                    return False
        except TimeoutException:
            print("time out")
            return False    
    
    elif language_type == "AWK":
        ori_path = os.getcwd()
        def compare_txt_files(file1, file2):
            """比较两个 txt 文件是否相同."""
            try:
                # 使用 filecmp 模块比较文件内容
    
                return filecmp.cmp(file1, file2, shallow=False)
            except FileNotFoundError as e:
                print(f"Error reading {file1} or {file2}: {e}")
                return False
        try:   
            with time_limit(timeout):
                # todo 对比文件结果
                awk_command = path
                with time_limit(timeout):
                    os.chdir('../')
                    # result = subprocess.check_output(
                    #     awk_command, shell=True)
                    result = subprocess.run([awk_command], shell=True)
                os.chdir(ori_path)
                # 将结果保存到1.txt文件
                file_path1 = os.path.join(temp_dir,"output.txt")
                with open(file_path1, "w") as file:
                    file.write(result.stdout)
                file_path2 = os.path.join(temp_dir, "awk"+task_id.split('/')[1]+'.txt')
                if compare_txt_files(file_path1, file_path2):
                    print("pass")
                    return True
                else:
                    print("error")
                    return False
        except TimeoutException:
            print("time out")
            os.chdir(ori_path)
            return False
        except Exception as e:
            print(traceback.print_exc())
            os.chdir(ori_path)
            return False
    elif language_type == "Erlang":
        try:
            # 编译 Erlang 程序的命令
            with time_limit(timeout):
                compile_command = ['erlc', path]
                module_name = path.split("/")[-1].split(".")[0]
                # print(module_name)
                # 运行测试的 Erlang 命令
                run_test_command = ['erl', '-noshell', '-s',
                                    module_name, 'test', '-s', 'init', 'stop']

                # 编译 Erlang 程序
                compile_result = subprocess.run(
                    compile_command)

                # 检查编译是否成功
                if compile_result.exit_code != 0:
                    print("编译失败:", compile_result.stdout)
                    return False
                else:
                    print("编译成功")

                    # 运行测试
                    run_test_result = subprocess.run(
                        run_test_command)

                    # 输出测试结果
                    #print("测试结果:\n", run_test_result.stdout)

                    # 判断测试是否成功
                    if run_test_result.exit_code == 0:
                        print("测试执行成功")
                        return True
                    else:
                        print("测试执行失败")
                        return False
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ["julia", "Julia"]:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['julia', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type == "Python":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['python', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type == "sql":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['python', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
        
    elif language_type.lower() in ["coffee", "coffeescript"]:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['coffee', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    print(run_result.stdout)
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ["kotlin", "Kotlin"]:
        try:
            exec_res = None
            with time_limit(timeout+10):
                run_result = subprocess.run(
                    ['kotlinc', '-script', path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ["php", "PHP"]:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['php', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                elif 'assert()' in run_result.stderr and 'failed' in run_result.stderr:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ['r', 'R']:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['Rscript', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ["ruby", 'Ruby']:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['ruby', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type in ["Java", 'java']:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['java', '-ea', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
                  
    elif language_type in ["cs", 'C_sharp', 'C#']:
        try:
            # print(path)
            project_path = path[:-11]
            # print('++++++++',project_path)
            with time_limit(timeout*2):
                run_result = subprocess.run(
                    ["dotnet", "run", "--project", project_path])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False
    elif language_type in ["fortran", "Fortran"]:
        try: 
            with time_limit(timeout):
            # 编译 fortran 程序的命令
                module_name = os.path.join(temp_dir, path.split("/")[1].split(".")[0])
        
                compile_command = ['gfortran', '-o', module_name, path]
                # print(module_name)
                # 运行测试的 fortran 命令
                run_test_command = [module_name]

                # 编译 fortran 程序
                compile_result = subprocess.run(
                    compile_command)

                # 检查编译是否成功
                if compile_result.exit_code != 0:
                    print("编译失败:", compile_result.stderr)
                    return False
                else:
                    print("编译成功")

                    # 运行测试
                    run_test_result = subprocess.run(
                        run_test_command)

                    # 判断测试是否成功
                    if run_test_result.exit_code != 0:
                        print("测试执行失败")
                        return False
                    elif 'failed' in run_test_result.stdout:
                        print("error 测试执行失败")
                        return False
                    else:
                        print("测试执行成功")
                        return True 
        except TimeoutException:
            print("time out")
            return False

    elif language_type == "Rust":
        try:
            ori_path = os.getcwd()
            os.chdir('./rust')
            subprocess.run(
                ['rm', '-rf', 'target'])
            with time_limit(timeout+20):
                time.sleep(1)
                run_result = subprocess.run(
                    ['cargo', 'test'])

                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    time.sleep(1)
                    os.chdir(ori_path)
                    return False
                else:
                    print("pass")
                    time.sleep(1)
                    os.chdir(ori_path)
                    return True

        except TimeoutException:
            print("time out") 
            time.sleep(1)
            os.chdir(ori_path) 
            return False

    elif language_type in ["scala", "Scala"]:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['scala', '-explain', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ["dart", 'Dart']:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['dart', 'run', '--enable-asserts', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type in ["groovy", "Groovy"]:
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['groovy', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    return False
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type == "C":
        try:
           
            module_name = os.path.join(temp_dir, path.split("/")[1].split(".")[0])
            compile_command = ['gcc', '-o', module_name, path, '-lm']
            # print(module_name)
            run_test_command = [module_name]
            compile_result = subprocess.run(
                compile_command)

            if compile_result.exit_code != 0:
                print("编译失败:", compile_result.stderr)
            else:
                print("编译成功")
                with time_limit(timeout):
                    # 运行测试
                    run_test_result = subprocess.run(
                        run_test_command)

                    # 输出测试结果
                    # print("测试结果:\n", run_test_result.stdout)

                    # 判断测试是否成功
                    if run_test_result.exit_code != 0:
                        print("测试执行失败")
                        print(run_test_result.stderr)
                    elif 'failed' in run_test_result.stdout:
                        print("error 测试执行失败")
                    else:
                        print("测试执行成功")
                        return True
        except TimeoutException:
            print("time out")
        return False

    elif language_type == "CPP":
        try:
            
            # print(path, path.split("/")[-1].split(".")[0])
            module_name = os.path.join(temp_dir, path.split("/")[-1].split(".")[0])
            compile_command = ['g++', '-g', '-std=c++11', '-o', module_name, path]

            # print(module_name)
        
            run_test_command = [module_name]

            # 编译 fortran 程序
            # compile_result = subprocess.run(compile_command)
            compile_result = subprocess.run(compile_command)

            # 检查编译是否成功
            if compile_result.exit_code != 0:
                print("编译失败:", compile_result.stderr)
            else:
                print("编译成功")
                with time_limit(timeout):
                    # 运行测试
                    run_test_result = subprocess.run(run_test_command)
                    output = run_test_result.stdout
                    # for encoding in ['utf-8', 'iso-8859-1', 'gbk']:
                    #     try:
                    #         output = run_test_result.stdout.decode(encoding)
                    #         break
                    #     except UnicodeDecodeError:
                    #         pass
                    # else:
                    #     raise UnicodeDecodeError('无法解码输出')
                    # 输出测试结果
                    # print("测试结果:\n", output)

                    # 判断测试是否成功
                    if run_test_result.exit_code != 0:
                        print("测试执行失败")
                        print(output)
                    elif 'failed' in output:
                        print("error 测试执行失败")
                    else:
                        print("测试执行成功")
                        return True
        except TimeoutException:
            print("time out")
        return False
    elif language_type == "Go":
        ori_path = os.getcwd()
        file_name = path.split('/')[-1]
        shutil.copy(path, './go/'+file_name)
        os.chdir('./go')
        try:
            with time_limit(timeout+20):
                run_result = subprocess.run(['go', 'test', file_name])
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    os.chdir(ori_path)
                    return False
                elif 'assert()' in  run_result.stderr and 'failed' in run_result.stderr:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                    os.chdir(ori_path)
                    return False
                else:
                    print("pass")
                    os.chdir(ori_path)
                    return True

        except TimeoutException:
            print("time out")
            os.chdir(ori_path)
        os.chdir(ori_path)
        return False

    elif language_type == "JavaScript":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['node', path])
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                elif 'failed' in run_result.stderr:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
        return False

    elif language_type == "TypeScript":
        try:
            exec_res = None
            with time_limit(timeout*2):
                compile_result = subprocess.run(
                    ['tsc', '--lib', 'es2015,dom', path])
                run_result = subprocess.run(
                    ['node', path.replace('.ts', '.js')])
                print(task_id)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                elif 'failed' in run_result.stderr:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
            return False

    elif language_type == "VimScript":
        try:
            exec_res = None
            with time_limit(timeout*2):
                run_result = subprocess.run(
                    ['vim', '-u', 'NONE', '-i', 'NONE', '-n', '-N', '--cmd', 'source '+path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                elif 'failed' in run_result.stderr:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
        except:
            traceback.print_exc()
            return False 
        return False

    elif language_type == "Lua":
        try:
            exec_res = None
            with time_limit(timeout):
                run_result = subprocess.run(
                    ['lua', path])
                print(task_id)
                # print(run_result)
                if run_result.exit_code != 0:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                elif 'failed' in run_result.stderr:
                    print("\nRun failed. Error message:")
                    print(run_result.stderr)
                else:
                    print("pass")
                    return True
        except TimeoutException:
            print("time out")
        return False

    elif language_type == "Pascal":
        try:
           
            module_name = os.path.join(temp_dir, path.split("/")[-1].split(".")[0])
            compile_command = ['fpc', path, '-MObjfpc']

    
            run_test_command = [module_name]

      
            compile_result = subprocess.run(
                compile_command)

            # 检查编译是否成功
            if compile_result.exit_code != 0:
                print("编译失败:", compile_result.stdout)
            else:
                print("编译成功")
                with time_limit(timeout):
                    # 运行测试
                    run_test_result = subprocess.run(
                        run_test_command)

                    # 输出测试结果
                    print("测试结果:\n", run_test_result.stdout)

                    # 判断测试是否成功
                    if run_test_result.exit_code != 0:
                        print("测试执行失败")
                        print(run_test_result.stderr)
                    elif 'failed' in run_test_result.stderr:
                        print("error 测试执行失败")
                    else:
                        print("测试执行成功")
                        return True
        except TimeoutException:
            print("time out")
        except:
            print(traceback.print_exc())
            print('error')
        return False
    else:
        print('can not found lang:', {language_type})


def get_awk_ans(item, temp_dir):
    
    try:
        with time_limit(timeout):
            # todo 对比文件结果
            awk_command = item['canonical_solution']
            with time_limit(timeout):
                # os.chdir('../')
                # result = subprocess.check_output(
                #     awk_command, shell=True)
                # result = raw_sub.check_output(['awk -F: \'$7 == "/bin/bash" {print $1}\' /etc/passwd'], shell=True)
                result = subprocess.run([awk_command], shell=True)
                # print(result.stdout)
                # os.chdir('./eval/')
                # print(result.stdout)
            # 将结果保存到1.txt文件
            # with open("tmp/awk"+item["task_id"].split('/')[1]+'.txt', "w") as file:
            with open(os.path.join(temp_dir, "awk"+item["task_id"].split('/')[1]+'.txt'), "w") as file:
                file.write(result.stdout)
            print(item["task_id"])
    except TimeoutException:
        print("time out")