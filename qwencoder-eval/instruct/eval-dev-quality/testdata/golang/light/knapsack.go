package light

import "math"

type Item struct {
	weight int
	value  int
}

func maximumValue(maximumWeight int, items []Item) int {
	knapsack := make([][]int, len(items)+1)
	for item := range knapsack {
		knapsack[item] = make([]int, maximumWeight+1)
		for weight := range knapsack[item] {
			knapsack[item][weight] = 0 // Return 0 if not filled
		}
	}

	for item := 0; item <= len(items); item++ {
		for weight := 0; weight <= maximumWeight; weight++ {
			if item == 0 || weight == 0 {
				knapsack[item][weight] = 0
			} else if items[item-1].weight > weight {
				knapsack[item][weight] = knapsack[item-1][weight]
			} else {
				itemValue := items[item-1].value
				itemWeight := items[item-1].weight
				knapsack[item][weight] = int(math.Max(float64(itemValue+knapsack[item-1][weight-itemWeight]), float64(knapsack[item-1][weight])))
			}
		}
	}

	return knapsack[len(items)][maximumWeight]
}
