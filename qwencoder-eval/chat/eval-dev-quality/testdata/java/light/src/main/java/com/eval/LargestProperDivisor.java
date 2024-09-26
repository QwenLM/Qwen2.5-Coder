// Copyright (C) rosettacode.org
package com.eval;

public class LargestProperDivisor {
  static int largestProperDivisor(int aNumber) {
    if (aNumber < 1) {
      throw new IllegalArgumentException("Argument must be >= 1: " + aNumber);
    }

    if ((aNumber & 1) == 0) {
      return aNumber >> 1;
    }
    for (int p = 3; p * p <= aNumber; p += 2) {
      if (aNumber % p == 0) {
        return aNumber / p;
      }
    }
    return 1;
  }
}
