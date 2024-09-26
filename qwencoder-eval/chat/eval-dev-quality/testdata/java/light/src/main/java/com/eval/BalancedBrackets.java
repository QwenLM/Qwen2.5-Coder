// Copyright (C) rosettacode.org
package com.eval;

public class BalancedBrackets {
  static boolean hasBalancedBrackets(char[] charArray) {
    int brackets = 0;
    for (char ch : charArray) {
      if (ch == '[') {
        brackets++;
      } else if (ch == ']') {
        brackets--;
      } else {
        return false; // Non-bracket characters.
      }
      if (brackets < 0) { // Closing bracket before opening bracket.
        return false;
      }
    }
    return brackets == 0;
  }
}
