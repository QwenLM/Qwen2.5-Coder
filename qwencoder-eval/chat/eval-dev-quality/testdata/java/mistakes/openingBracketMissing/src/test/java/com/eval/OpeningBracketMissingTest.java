package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class OpeningBracketMissingTest {
	@Test
	public void openingBracketMissing1() {
		int x = -1;
		int expected = -1;
		int actual = OpeningBracketMissing.openingBracketMissing(x);

		assertEquals(expected, actual);
	}

	@Test
	public void openingBracketMissing2() {
		int x = 0;
		int expected = 0;
		int actual = OpeningBracketMissing.openingBracketMissing(x);

		assertEquals(expected, actual);
	}

	@Test
	public void openingBracketMissing3() {
		int x = 1;
		int expected = 1;
		int actual = OpeningBracketMissing.openingBracketMissing(x);

		assertEquals(expected, actual);
	}
}
