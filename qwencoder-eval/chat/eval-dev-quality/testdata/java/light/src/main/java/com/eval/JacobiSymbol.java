// Copyright (C) rosettacode.org
package com.eval;

public class JacobiSymbol {
  static int jacobiSymbol(int k, int n) {
    if (k < 0 || n % 2 == 0) {
      throw new IllegalArgumentException("Invalid value. k = " + k +
          ", n = " + n);
    }
    k %= n;
    int jacobi = 1;
    while (k > 0) {
      while (k % 2 == 0) {
        k /= 2;
        int r = n % 8;
        if (r == 3 || r == 5) {
          jacobi = -jacobi;
        }
      }
      int temp = n;
      n = k;
      k = temp;
      if (k % 4 == 3 && n % 4 == 3) {
        jacobi = -jacobi;
      }
      k %= n;
    }
    if (n == 1) {
      return jacobi;
    }
    return 0;
  }
}
