package com.eval;

public class PhoneNumber {
  static String extractDigits(String dirtyNumber) {
    String cleanNumber = "";
    for (int i = 0; i < dirtyNumber.length(); i++) {
      char c = dirtyNumber.charAt(i);
      if (c == ' ' || c == '.' || c == '(' || c == ')' || c == '-' ||
          c == '+') {
        // Remove spaces, dots, parentheses, hyphens and pluses.
        continue;
      }
      if (c == '-' || c == '@' || c == ':' || c == '!') {
        throw new IllegalArgumentException("punctuations not permitted");
      }
      if (c < '0' || c > '9') {
        throw new IllegalArgumentException("letters not permitted");
      }
      cleanNumber += c;
    }

    return cleanNumber;
  }
}
