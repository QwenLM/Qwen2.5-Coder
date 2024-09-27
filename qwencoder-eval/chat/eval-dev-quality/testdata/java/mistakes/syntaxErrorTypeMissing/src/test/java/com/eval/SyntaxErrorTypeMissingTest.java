package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class SyntaxErrorTypeMissingTest {
	@Test
	public void syntaxErrorTypeMissing1() {
		int x = -1;
		int expected = -1;
		int actual = SyntaxErrorTypeMissing.syntaxErrorTypeMissing(x);

		assertEquals(expected, actual);
	}

	@Test
	public void syntaxErrorTypeMissing2() {
		int x = 0;
		int expected = 0;
		int actual = SyntaxErrorTypeMissing.syntaxErrorTypeMissing(x);

		assertEquals(expected, actual);
	}

	@Test
	public void syntaxErrorTypeMissing3() {
		int x = 1;
		int expected = 1;
		int actual = SyntaxErrorTypeMissing.syntaxErrorTypeMissing(x);

		assertEquals(expected, actual);
	}
}
