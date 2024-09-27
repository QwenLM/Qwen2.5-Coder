// Copyright (C) rosettacode.org
package com.eval;

public class EqulibriumIndices {
  static String equlibriumIndices(int[] sequence) {
    String indexList = "";
    // Determine total sum.
    int totalSum = 0;
    for (int n : sequence) {
      totalSum += n;
    }
    // Compare running sum to remaining sum to find equilibrium indices.
    int runningSum = 0;
    for (int i = 0; i < sequence.length; i++) {
      int n = sequence[i];
      if (totalSum - runningSum - n == runningSum) {
        indexList += i + ";";
      }
      runningSum += n;
    }

    return indexList;
  }
}
