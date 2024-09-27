package com.eval;

public class CollatzCalculator {
  static int computeStepCount(final int start) {
    if (start <= 0) {
      throw new IllegalArgumentException("Only positive integers are allowed");
    }
    if (start == 1) {
      return 0;
    }
    final int next;

    if (start % 2 == 0) {
      next = start / 2;
    } else {
      next = 3 * start + 1;
    }

    return 1 + computeStepCount(next);
  }
}
