language_symbols = {
    "python": {
        "CLASS_TYPE": "class_definition",
        "FUNCTION_TYPE": "function_definition",
        "IMPORT_TYPE": ["import_statement", "import_from_statement"],
        "IDENTIFIER_TYPE": "identifier",
        "ATTRIBUTE_TYPE": "attribute",
        "RETURN_TYPE": "return_statement",
        "EXPRESSION_TYPE": "expression_statement",
        "ASSIGNMENT_TYPE": "assignment"
    },
    "java": {
        "CLASS_TYPE": "class_definition",
        "FUNCTION_TYPE": "function_definition",
        "IMPORT_TYPE": ["import_statement", "import_from_statement"],
        "IDENTIFIER_TYPE": "identifier",
        "ATTRIBUTE_TYPE": "attribute",
        "RETURN_TYPE": "return_statement",
        "EXPRESSION_TYPE": "expression_statement",
        "ASSIGNMENT_TYPE": "assignment"
    },
    "c-sharp": {
        "CLASS_TYPE": "class_definition",
        "FUNCTION_TYPE": "function_definition",
        "IMPORT_TYPE": ["import_statement", "import_from_statement"],
        "IDENTIFIER_TYPE": "identifier",
        "ATTRIBUTE_TYPE": "attribute",
        "RETURN_TYPE": "return_statement",
        "EXPRESSION_TYPE": "expression_statement",
        "ASSIGNMENT_TYPE": "assignment"
    },
    "typescript": {
        "CLASS_TYPE": "class_definition",
        "FUNCTION_TYPE": "function_definition",
        "IMPORT_TYPE": ["import_statement", "import_from_statement"],
        "IDENTIFIER_TYPE": "identifier",
        "ATTRIBUTE_TYPE": "attribute",
        "RETURN_TYPE": "return_statement",
        "EXPRESSION_TYPE": "expression_statement",
        "ASSIGNMENT_TYPE": "assignment"
    }
}

def guess_lang(code):
    characteristics = {
        "python": [
            "break", "class ", "continue", "def ", "del ", "elif ", "else ",
            "except", "finally", "for ", "from ", "global ", "if ", "import",
            "lambda", "nonlocal", "pass", "raise",
            "return", "try", "while", "with", "yield",
            "def ", "import ", "as ", "lambda ", "print(", "class ", "self.", "raise ", "except", "python"
        ],
        "c++": [
            "#include <", "std::", "cout <<", "cin >>", "namespace ", "NULL", "std::vector<", "std::string", "template<", "::"
        ],
        "java": [
            "public class ", "public static void main", "System.out.println", "import java.", "extends ", "implements ", "new ", "throws ", "// "
        ],
        "php": [
            "<?php", "echo ", "<?= ", "$", "public function ", "array(", "class ", ";", "?>"
        ],
        "typescript": [
            "interface ", "let ", ": number", "=>", "enum ", "type ", "public ", "private ", "protected ", "import "
        ],
        "r": [
            "<-", "library(", "data.frame(", "ggplot(", "plot(", "function(", " <-", " c(", "list("
        ],
        "swift": [
            "let ", "var ", "func ", "import SwiftUI", "struct ", "enum ", "class ", "override ", "extension ", "self."
        ],
        "rust": [
            "fn ", "let ", "mut ", "use std::", "impl ", "#[derive(", "match ", "pub struct ", "mod ", "extern crate "
        ],
        "go": [
            "package ", "import ", "func ", "var ", "const ", "type ", "chan ", "defer ", "go func", "map["
        ],
        "C#": [
            "using System;", "static void Main", "Console.WriteLine", "public class ", "namespace ", "get; set;", "[", "/*"
        ],
        "Bash": [
            "#!/bin/bash", "echo ", "grep ", "function ", "if ", "then ", "fi", "do", "done", "case in", "export ", "`"
        ],
        "jupyter": [
            "%matplotlib inline", "import pandas as pd", "# In[", "plt.plot(", "pd.DataFrame(", "!pip install ", "%load_ext"
        ]
    }
    for language, signs in characteristics.items():
        code_tokens = code.split()
        key_words = set(signs) & set(code_tokens)
        if len(key_words) > 0:
            return language, ", ".join(key_words)
    return "unknown", None
