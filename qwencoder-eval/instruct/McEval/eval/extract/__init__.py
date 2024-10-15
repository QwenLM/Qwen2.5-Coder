from .extract_coffescript_code import extract_coffeescript_code
from .extract_fortran_code import extract_fortran_code
from .extract_csharp_code import extract_csharp_code
from .extract_dart_code import extract_dart_code
from .extract_groovy_code import extract_groovy_code
from .extract_java_code import extract_java_code
from .extract_julia_code import extract_julia_code
from .extract_kotlin_code import extract_kotlin_code
from .extract_php_code import extract_php_code
from .extract_python_code import extract_python_code
from .extract_r_code import extract_r_code
from .extract_ruby_code import extract_ruby_code
from .extract_rust_code import extract_rust_code
from .extract_scala_code import extract_scala_code
from .extract_c_code import extract_ccpp_code
from .extract_javascript_code import extract_js_code
from .extract_typescript_code import extract_ts_code
from .extract_lua_code import extract_lua_code
from .extract_vimscript_code import extract_vimscript_code
from .extract_go_code import extract_go_code
from .extract_pascal_code import extract_pascal_code
from .extract_clisp_code import extract_clisp_code
from .extract_elisp_code import extract_elisp_code
from .extract_elixir_code import extract_elixir_code
from .extract_erlang_code import extract_erlang_code
from .extract_racket_code import extract_racket_code
from .extract_scheme_code import extract_scheme_code
from .extract_haskell_code import extract_haskell_code
from .extract_shell_code import extract_shell_code
from .extract_powershell_code import extract_powershell_code
from .extract_swift_code import extract_swift_code
from .extract_vb_code import extract_vb_code
from .extract_fs_code import extract_fs_code
from .extract_perl_code import extract_perl_code
from .extract_tcl_code import extract_tcl_code
from .extract_json_code import extract_json_code
from .extract_markdown_code import extract_md_code
from .extract_html_code import extract_html_code
from .extract_awk_code import extract_awk_code
# langs = [
#     'Coffeescript', 'Dart', 'Fortran', 'Go', 'Groovy', 'java', 'Julia',
#     'Kotlin', 'PHP', 'Python', 'R', 'ruby', 'Rust', 'Scala'

# ]


def extract(text, item, lang):
    if lang.lower() in ['coffeescript']:
        return extract_coffeescript_code(text, item)
    elif lang.lower() == 'dart':
        return extract_dart_code(text, item)
    elif lang.lower() == 'fortran':
        return extract_fortran_code(text, item)
    elif lang.lower() in ['c_sharp', 'cs', 'c#']:
        return extract_csharp_code(text, item)
    elif lang.lower() == 'go':
        return extract_go_code(text, item)
    elif lang.lower() == 'groovy':
        return extract_groovy_code(text, item)
    elif lang.lower() == 'java':
        return extract_java_code(text, item)
    elif lang.lower() == 'julia':
        return extract_julia_code(text, item)
    elif lang.lower() == 'kotlin':
        return extract_kotlin_code(text, item)
    elif lang.lower() == 'php':
        return extract_php_code(text, item)
    elif lang.lower() == 'python':
        return extract_python_code(text, item)
    elif lang.lower() == 'r':
        return extract_r_code(text, item)       
    elif lang.lower() == 'ruby':
        return extract_ruby_code(text, item)       
    elif lang.lower() == 'rust':
        return extract_rust_code(text, item)   
    elif lang.lower() == 'scala':
        return extract_scala_code(text, item) 
    elif lang == 'C' or lang == 'CPP':
        return extract_ccpp_code(text, item)
    elif lang == 'JavaScript':
        return extract_js_code(text, item)
    elif lang == 'TypeScript':
        return extract_ts_code(text, item)
    elif lang == 'Lua':
        return extract_lua_code(text, item)
    elif lang == 'VimScript':
        return extract_vimscript_code(text, item)
    elif lang == 'Pascal':
        return extract_pascal_code(text, item)
    elif lang == 'Common Lisp':
        return extract_clisp_code(text, item)
    elif lang == 'Emacs Lisp':
        return extract_elisp_code(text, item)
    elif lang == 'Elixir':
        return extract_elixir_code(text, item)
    elif lang == 'Erlang':
        return extract_erlang_code(text, item)
    elif lang == 'Racket':
        return extract_racket_code(text, item)
    elif lang == 'Scheme':
        return extract_scheme_code(text, item)
    elif lang == 'Haskell':
        return extract_haskell_code(text, item)
    elif lang == 'Shell':
        return extract_shell_code(text, item)
    elif lang == 'PowerShell':
        return extract_powershell_code(text, item)
    elif lang == 'Swift':
        return extract_swift_code(text, item)
    elif lang == 'Visual Basic':
        return extract_vb_code(text, item)
    elif lang == 'F#':
        return extract_fs_code(text, item)
    elif lang == 'Perl':
        return extract_perl_code(text, item)
    elif lang == 'Tcl':
        return extract_tcl_code(text, item)
    elif lang == 'JSON':
        return extract_json_code(text)
    elif lang == 'Markdown':
        return extract_md_code(text)
    elif lang == 'HTML':
        return extract_html_code(text)
    elif lang == 'AWK':
        # print(extract_awk_code(text))
        return extract_awk_code(text)
    else:
        print("Language not supported:", lang)  