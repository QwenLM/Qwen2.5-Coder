package light

import "strconv"

func equilibriumIndices(sequence []int) (indexList string) {
	// Determine total sum.
	var totalSum int
	for _, n := range sequence {
		totalSum += n
	}
	// Compare running sum to remaining sum to find equilibrium indices.
	var runningSum int
	for i, n := range sequence {
		if totalSum-runningSum-n == runningSum {
			indexList += strconv.Itoa(i) + ";"
		}
		runningSum += n
	}

	return indexList
}
