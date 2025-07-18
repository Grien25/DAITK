#include "__mem.h"
#include <stddef.h>

// Decompiled from auto_00_80004000_init.s
// Reference: DecompReference/rb3/src/sdk/PowerPC_EABI_Support/Runtime/__mem.c

void* memcpy(void* dest, const void* src, size_t count) {
    unsigned char* d = (unsigned char*)dest;
    const unsigned char* s = (const unsigned char*)src;
    if (d == s || count == 0) return dest;
    if (s > d) {
        // Forward copy
        for (size_t i = 0; i < count; ++i) {
            d[i] = s[i];
        }
    } else {
        // Backward copy (overlap)
        for (size_t i = count; i > 0; --i) {
            d[i - 1] = s[i - 1];
        }
    }
    return dest;
}

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

void* memset(void* dest, int ch, size_t count) {
    __fill_mem(dest, ch, count);
    return dest;
} 

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyD1maEHkPkJvIokonRLV-FJvwCrLWJXMFk]

[Gemini API error: missing API key]

[Gemini API error: missing API key]

[Gemini API error: missing API key]

```c
#include <stddef.h>

// Copies count bytes from src to dest.
// Returns a pointer to dest.
void* memcpy(void* dest, const void* src, size_t count) {
    char* d = (char*)dest;
    const char* s = (const char*)src;

    // If count is zero, just return.
    if (count == 0) {
        return dest;
    }

    // If dest < src, copy forwards
    if (dest < src) {
        if ((unsigned long)d % 32 == (unsigned long)s % 32) {
            if (count >= 128) {
                // Optimized copy with dcbt (data cache block touch) instruction
                size_t alignedCount = count & ~0x7F; // round down to nearest multiple of 128
                size_t i;

                dcbt(0, d);

                // Optimized loop for copying 128 bytes at a time.
                size_t iterations = alignedCount >> 5; // divide by 32
                for(i = 0; i < iterations; i++) {
                    double f1 = *((double*)s);
                    double f2 = *((double*)(s + 8));
                    double f3 = *((double*)(s + 16));
                    double f4 = *((double*)(s + 24));

                    s += 32;

                    *((double*)d) = f1;
                    *((double*)(d + 8)) = f2;
                    *((double*)(d + 16)) = f3;
                    *((double*)(d + 24)) = f4;

                    d += 32;
                }
                count &= 0x1F;

                //Copy remaining bytes
                for(; count > 0; count--, s++, d++) {
                    *d = *s;
                }
                return dest;

            } else if(count >= 20) {
                // copy 4 words at a time
                size_t alignedCount = count & ~0x0F; // round down to nearest multiple of 16
                size_t i;

                // Optimized loop for copying 16 bytes at a time.
                size_t iterations = alignedCount >> 4;
                for(i = 0; i < iterations; i++) {
                    int w1 = *((int*)s);
                    int w2 = *((int*)(s + 4));
                    int w3 = *((int*)(s + 8));
                    int w4 = *((int*)(s + 12));

                    s += 16;

                    *((int*)d) = w1;
                    *((int*)(d + 4)) = w2;
                    *((int*)(d + 8)) = w3;
                    *((int*)(d + 12)) = w4;

                    d += 16;
                }

                count &= 0xF;

                //Copy remaining bytes
                for(; count > 0; count--, s++, d++) {
                    *d = *s;
                }
                return dest;

            }
        }


        // basic byte copy if no alignment and count conditions are met.
        for (; count > 0; count--) {
            *d++ = *s++;
        }
    } else {
        // dest > src, copy backwards
        d += count;
        s += count;

        if(count >= 128) {
            size_t alignedCount = count & ~0x7F;
            d -= alignedCount;
            s -= alignedCount;
            size_t i;

            size_t iterations = alignedCount >> 5;

            for(i = 0; i < iterations; i++) {
                d -= 32;
                s -= 32;

                double f1 = *((double*)s);
                double f2 = *((double*)(s + 8));
                double f3 = *((double*)(s + 16));
                double f4 = *((double*)(s + 24));

                *((double*)d) = f1;
                *((double*)(d + 8)) = f2;
                *((double*)(d + 16)) = f3;
                *((double*)(d + 24)) = f4;

            }

            count &= 0x1F;

        } else if(count >= 20) {
            //Copy 4 words at a time backwards
            size_t alignedCount = count & ~0x0F;
            d -= alignedCount;
            s -= alignedCount;
            size_t i;

            size_t iterations = alignedCount >> 4;

            for(i = 0; i < iterations; i++) {
                d -= 16;
                s -= 16;

                int w1 = *((int*)s);
                int w2 = *((int*)(s + 4));
                int w3 = *((int*)(s + 8));
                int w4 = *((int*)(s + 12));

                *((int*)d) = w1;
                *((int*)(d + 4)) = w2;
                *((int*)(d + 8)) = w3;
                *((int*)(d + 12)) = w4;
            }

            count &= 0xF;
        }

        // basic byte copy if no alignment and count conditions are met.
        for (; count > 0; count--) {
            *--d = *--s;
        }
    }
    return dest;
}
```

```c
#include <stddef.h>

void* memset(void* dest, int ch, size_t count) {
    // The assembly calls __fill_mem and then returns dest.
    extern void __fill_mem(void* dest, int ch, size_t count); // Declare the external function

    __fill_mem(dest, ch, count);
    return dest;
}
```