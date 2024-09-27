package com.eval;

public class OpeningBracketMissing {
	public static int openingBracketMissing(int x)
		if (x > 0) {
			return 1;
		}
		if (x < 0) {
			return -1;
		}

		return 0;
	}
}
