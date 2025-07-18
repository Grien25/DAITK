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