package light

func matchBytes(s1 []byte, s2 []byte) bool {
	for i := 0; i < len(s1); i++ {
		c1 := s1[i]
		c2 := s2[i]

		if c1 != c2 {
			c1 |= 'a' - 'A'
			c2 |= 'a' - 'A'

			if c1 != c2 || c1 < 'a' || c1 > 'z' {
				return false
			}
		}
	}

	return true
}
