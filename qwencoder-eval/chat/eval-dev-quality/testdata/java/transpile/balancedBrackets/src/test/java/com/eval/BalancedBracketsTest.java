package com.eval;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class BalancedBracketsTest {
	@Test
	public void hasBalancedBrackets1() {
		char[] charArray = {};
		boolean actual = BalancedBrackets.hasBalancedBrackets(charArray);

		assertTrue(actual);
	}

	@Test
	public void hasBalancedBrackets2() {
		char[] charArray = { '[' };
		boolean actual = BalancedBrackets.hasBalancedBrackets(charArray);

		assertFalse(actual);
	}

	@Test
	public void hasBalancedBrackets3() {
		char[] charArray = { '[', '[', '[', ']', ']' };
		boolean actual = BalancedBrackets.hasBalancedBrackets(charArray);

		assertFalse(actual);
	}

	@Test
	public void hasBalancedBrackets4() {
		char[] charArray = { '[', '[', ']', ']' };
		boolean actual = BalancedBrackets.hasBalancedBrackets(charArray);

		assertTrue(actual);
	}

	@Test
	public void hasBalancedBrackets5() {
		char[] charArray = { '[', '[', '[', '[', ']', ']', ']', ']' };
		boolean actual = BalancedBrackets.hasBalancedBrackets(charArray);

		assertTrue(actual);
	}
}
