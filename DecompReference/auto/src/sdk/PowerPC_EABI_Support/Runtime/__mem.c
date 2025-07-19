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

[Gemini API error: 503 Server Error: Service Unavailable for url: https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key=AIzaSyDIkQe9MOnjVxcbF56bVASvXSNifdDGQlU]

```c
#include <stddef.h>

// Fills a memory region with a specified value.
// dest: Pointer to the destination memory region.
// ch: Value to fill the memory with (treated as an int).
// count: Number of bytes to fill.
void* memset(void* dest, int ch, size_t count) {
    // r3 -> dest
    // r4 -> ch
    // r5 -> count
    // r31 -> saved dest
    // Calls __fill_mem(dest, ch, count) to perform the actual filling.
    // Returns the original destination pointer (dest).

    // The assembly saves r31, calls __fill_mem, restores r31, and returns r31 which is dest.
    __fill_mem(dest, ch, count);
    return dest;
}
```

```c
#include <stddef.h>
#include <stdint.h>

void* memcpy(void* dest, const void* src, size_t count) {
    unsigned char* d = (unsigned char*)dest;
    const unsigned char* s = (const unsigned char*)src;

    // Early out if count is zero
    if (count == 0) {
        return dest;
    }

    // Check if dest < src
    if (d < s) {
        // Check if src + count > dest
        if ((uintptr_t)s < (uintptr_t)d + count) {
          if ((uintptr_t)s == (uintptr_t)d) {
            goto forward_copy;
          }

            // If source and destination overlap, but destination is before source,
            // copy forward if source is aligned enough
            goto byte_copy_forward;
        }

        if (count >= 0x80) {
          //Align source and destination

          //Calculate Alignment
          uintptr_t src_aligned = (uintptr_t)s & 0x7;
          uintptr_t dst_aligned = (uintptr_t)d & 0x7;

          //If alignment does not match, copy 1 byte at a time until they are aligned
          if (src_aligned != dst_aligned) {
            goto byte_copy_forward;
          }

          //Calculate remainder
          size_t remainder = count;

          remainder -= src_aligned > 8 ? 8 : src_aligned;
          
          size_t doubleword_count = remainder >> 5;

          //Copy 32 bytes (4 doubles) at a time
          for (size_t i = 0; i < doubleword_count; i++) {
              double f1 = *(double*)s;
              double f2 = *(double*)((uintptr_t)s + 8);
              double f3 = *(double*)((uintptr_t)s + 16);
              double f4 = *(double*)((uintptr_t)s + 24);

              *(double*)d = f1;
              *(double*)((uintptr_t)d + 8) = f2;
              *(double*)((uintptr_t)d + 16) = f3;
              *(double*)((uintptr_t)d + 24) = f4;

              d += 32;
              s += 32;
          }

          remainder = count & 0x1f;

          if (remainder == 0) {
            goto return_dest;
          }

          goto byte_copy_forward_remainder;
          
        }
        else {
          goto byte_copy_forward;
        }

forward_copy:
        // Simple forward byte copy
byte_copy_forward:
        for (size_t i = 0; i < count; i++) {
          d[i] = s[i];
        }
byte_copy_forward_remainder:
        for (size_t i = 0; i < count; i++) {
          d++;
          s++;
          *d = *s;
        }
    } else {
        // Dest >= src, copy backwards

        // Check if dest < src + count
        if ((uintptr_t)d < (uintptr_t)s + count) {

          if ((uintptr_t)s == (uintptr_t)d) {
            goto backward_copy;
          }

            //If source and destination overlap, copy backward
            goto byte_copy_backward;
        }

        //If count is greater than or equal to 0x80, copy big chunks at a time.
        if (count >= 0x80) {
          //Align source and destination

          //Calculate Alignment
          uintptr_t src_aligned = (uintptr_t)s & 0x7;
          uintptr_t dst_aligned = (uintptr_t)d & 0x7;

          //If alignment does not match, copy 1 byte at a time until they are aligned
          if (src_aligned != dst_aligned) {
            goto byte_copy_backward;
          }

          //Calculate remainder
          size_t remainder = count;

          size_t aligned_start = remainder & 0x7;

          remainder -= aligned_start > 8 ? 8 : aligned_start;

          //Copy 32 bytes (4 doubles) at a time
          size_t doubleword_count = remainder >> 5;

          d += count;
          s += count;
          
          for (size_t i = 0; i < doubleword_count; i++) {
              d -= 32;
              s -= 32;
              double f1 = *(double*)s;
              double f2 = *(double*)((uintptr_t)s + 8);
              double f3 = *(double*)((uintptr_t)s + 16);
              double f4 = *(double*)((uintptr_t)s + 24);

              *(double*)d = f1;
              *(double*)((uintptr_t)d + 8) = f2;
              *(double*)((uintptr_t)d + 16) = f3;
              double* d4_ptr = (double*)((uintptr_t)d + 24);
              *d4_ptr = f4;
          }

          remainder = count & 0x1f;

          if (remainder == 0) {
            goto return_dest;
          }

          goto byte_copy_backward_remainder;
        }
        else{
          goto byte_copy_backward;
        }

backward_copy:
        // Simple backward byte copy
byte_copy_backward:
        d += count;
        s += count;
        for (size_t i = 0; i < count; i++) {
          d--;
          s--;
          *d = *s;
        }
byte_copy_backward_remainder:
        d += count;
        s += count;
        for (size_t i = 0; i < count; i++) {
          d--;
          s--;
          *d = *s;
        }
    }

return_dest:
    return dest;
}
```