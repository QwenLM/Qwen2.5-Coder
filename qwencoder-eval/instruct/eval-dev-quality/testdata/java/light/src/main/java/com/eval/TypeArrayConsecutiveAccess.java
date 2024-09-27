package com.eval;

class TypeArrayConsecutiveAccess {
    static int typeArrayConsecutiveAccess(int[] input) {
        int cnt = 0;
        if (input[0] == 0)
            cnt++;
        if (input[1] == 8)
            cnt++;
        return cnt;
    }
}
