package light

func forLoop(s int) int {
	sum := 0
	for i := 0; i < s; i++ {
		sum = sum + i
	}
	for i := 0; i < s; i++ {
		sum = sum + i
	}

	return sum
}
