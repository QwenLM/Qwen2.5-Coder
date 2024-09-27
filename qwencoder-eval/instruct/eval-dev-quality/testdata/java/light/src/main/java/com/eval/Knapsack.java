package com.eval;

public class Knapsack {
  static int maximumValue(int maximumWeight, Item[] items) {
    int[][] knapsack = new int[items.length + 1][maximumWeight + 1];
    for (int item = 0; item <= items.length; item++) {
      for (int weight = 0; weight <= maximumWeight; weight++) {
        knapsack[item][weight] = 0; // Return 0 if not filled
      }
    }
    for (int item = 0; item <= items.length; item++) {
      for (int weight = 0; weight <= maximumWeight; weight++) {
        if (item == 0 || weight == 0) {
          knapsack[item][weight] = 0;
        } else if (items[item - 1].weight > weight) {
          knapsack[item][weight] = knapsack[item - 1][weight];
        } else {
          int itemValue = items[item - 1].value;
          int itemWeight = items[item - 1].weight;
          knapsack[item][weight] =
              Math.max(itemValue + knapsack[item - 1][weight - itemWeight],
                       knapsack[item - 1][weight]);
        }
      }
    }
    return knapsack[items.length][maximumWeight];
  }

  static class Item {
    int weight;
    int value;
  }
}
