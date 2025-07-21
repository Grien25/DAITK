```c
#include <stddef.h> // Include for size_t
#include <stdint.h>
```c

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

          remainder = remainder & 0x1f;

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
        for (size_t i = 0; i < remainder; i++) {
          *d = *s;
          d++;
          s++;
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

          remainder = remainder & 0x1f;

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
        for (size_t i = 0; i < count; i++) {
          d += count - 1 - i;
          s += count - 1 - i;
          *d = *s;
          d = (unsigned char*)dest;
          s = (const unsigned char*)src;
        }
byte_copy_backward_remainder:
        d += count;
        s += count;
        for (size_t i = 0; i < remainder; i++) {
          d--;
          s--;
          *d = *s;
        }
    }

return_dest:
    return dest;
}

// memset implementation for the Nintendo Wii (circa 2006)
// This implementation leverages an internal __fill_mem function for the actual memory filling.
void* memset(void* dest, int ch, size_t count) {
    // r3 -> dest, r4 -> ch, r5 -> count
    __fill_mem(dest, ch, count); // Call internal fill function
    return dest; // Return the destination pointer
}


void __fill_mem(void* dest, int ch, size_t count) {
    // r3: dest (void*)
    // r4: ch (int)
    // r5: count (size_t)
    // r6: dest - 1 (char*)
    // r7: ch & 0xFF (uint8_t)
    // r0: temporary register

    if (count < 0x20) {
        // Handle small counts byte-by-byte
        uint8_t byte_val = (uint8_t)(ch & 0xFF); // Extract the lowest byte of the int
        char* p = (char*)dest - 1;
        size_t i = count;
        while (i > 0) {
            p++;
            *p = byte_val;
            i--;
        }
        return;
    }

    uint8_t byte_val = (uint8_t)(ch & 0xFF);
    char* p = (char*)dest - 1;
    size_t byte_count = count;

    if (byte_val == 0) {
        // Create a word filled with ch if ch is 0
        ch = 0;
    } else {
        // Fill the word with ch
        ch = byte_val;
        ch |= ch << 8;
        ch |= ch << 16;
    }
    
    if ((count >> 5) == 0) {
        // Handle remaining bytes that are not divisible by 32
    } else {
        ptrdiff_t long_count = count >> 5; // Number of 32 byte blocks
        char* p_long = (char*)dest - 3;

        while (long_count > 0)
        {
            *((uint32_t*)(p_long + 4)) = ch;
            *((uint32_t*)(p_long + 8)) = ch;
            *((uint32_t*)(p_long + 12)) = ch;
            *((uint32_t*)(p_long + 16)) = ch;
            *((uint32_t*)(p_long + 20)) = ch;
            *((uint32_t*)(p_long + 24)) = ch;
            *((uint32_t*)(p_long + 28)) = ch;
            p_long += 32;
            *((uint32_t*)(p_long)) = ch;
        }
    }

    if (((count >> 3) & 0x7) == 0) {

    }
    else {
        ptrdiff_t extr_count = ((count >> 3) & 0x7);
        char* p_extr = (char*)dest - 3;
        while (extr_count > 0) {
           *((uint32_t*)(p_extr + 4)) = ch;
           p_extr += 8;
           extr_count--;
        }
    }

    // Handle the remaining bytes.
    ptrdiff_t add = 3;
    p = (char*)dest + add;
    byte_count = count & 0x7;

    while (byte_count > 0) {
        p--;
        *p = byte_val;
        byte_count--;
    }
    return;
}
```
