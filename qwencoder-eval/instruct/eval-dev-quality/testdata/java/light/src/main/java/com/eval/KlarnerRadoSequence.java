// Copyright (C) rosettacode.org
package com.eval;

public class KlarnerRadoSequence {
  static int[] initialiseKlarnerRadoSequence(int limit) {
    int[] result = new int[limit + 1];
    int i2 = 1, i3 = 1;
    int m2 = 1, m3 = 1;
    for (int i = 1; i <= limit; i++) {
      int minimum = Math.min(m2, m3);
      result[i] = minimum;
      ;
      if (m2 == minimum) {
        m2 = result[i2] * 2 + 1;
        i2 += 1;
      }
      if (m3 == minimum) {
        m3 = result[i3] * 3 + 1;
        i3 += 1;
      }
    }
    return result;
  }
}
