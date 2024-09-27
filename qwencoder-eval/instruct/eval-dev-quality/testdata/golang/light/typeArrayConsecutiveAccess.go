package light

func typeArrayConsecutiveAccess(input []int) int {
	cnt := 0
	if input[0] == 0 {
		cnt++
	}
	if input[1] == 8 {
		cnt++
	}
	return cnt
}
