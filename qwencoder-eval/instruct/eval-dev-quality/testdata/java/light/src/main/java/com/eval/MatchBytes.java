package com.eval;

class MatchBytes {
    static boolean matchBytes(byte[] s1, byte[] s2) {
		for (int i = 0; i < s1.length; i++) {
			byte c1 = s1[i];
			byte c2 = s2[i];

			if (c1 != c2) {
				c1 |= 'a' - 'A';
				c2 |= 'a' - 'A';

				if (c1 != c2 || c1 < 'a' || c1 > 'z') {
					return false;
				}
			}
		}

		return true;
	}
}
