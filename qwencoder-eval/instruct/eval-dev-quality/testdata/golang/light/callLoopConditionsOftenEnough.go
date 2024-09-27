package light

func callLoopConditionsOftenEnough(x, y int) int {
	if x < 10 || x > 20 {
		return 0
	}

	for i := 0; i < y; i++ {
		if i > 20 {
			x++ // This needs to be executed more than 10 times
		}
	}

	if x > 20 { // This block needs to be reached for full coverage
		x = x / 2
	}

	return x
}
