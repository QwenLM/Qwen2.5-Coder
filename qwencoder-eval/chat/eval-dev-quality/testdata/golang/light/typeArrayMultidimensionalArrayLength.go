package light

func typeArrayMultidimensionalArrayLength(x [][]int) int {
	if len(x) == 2 {
		if len(x[0]) == 2 {
			return 2
		}

		return 1
	}

	return 0
}
