package light

func binarySearch(a []int, x int) int {
	index := -1

	min := 0
	max := len(a) - 1

	for index == -1 && min <= max {
		m := (min + max) / 2

		if x == a[m] {
			index = m
		} else if x < a[m] {
			max = m - 1
		} else {
			min = m + 1
		}
	}

	return index
}
