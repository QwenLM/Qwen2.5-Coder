package balancedBrackets

func hasBalancedBrackets(charArray string) bool {
	brackets := 0
	for _, ch := range charArray {
		if ch == '[' {
			brackets++
		} else if ch == ']' {
			brackets--
		} else {
			return false // Non-bracket characters.
		}
	}

	if brackets < 0 { // Closing bracket before opening bracket.
		return false
	}

	return brackets == 0
}
