package variableUnknown

func variableUnknown(x int) int {
	y = x
	if x > 0 {
		return y
	}
	if x < 0 {
		return -y
	}

	return 0
}
