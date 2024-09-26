package com.eval;

class ForLoop {
    static int forLoop(int s) {
        int sum = 0;
        for (int i = 0; i < s; i++) {
            sum = sum + i;
        }
        for (int i = 0; i < s; i++) {
            sum = sum + i;
        }

        return sum;
    }
}
