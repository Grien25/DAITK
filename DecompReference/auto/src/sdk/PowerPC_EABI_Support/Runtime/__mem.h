#ifndef AUTO_MEM_H
#define AUTO_MEM_H

#include <stddef.h>

void* memcpy(void* dest, const void* src, size_t count);
void* memset(void* dest, int ch, size_t count);
void __fill_mem(void* dest, int ch, size_t count);

#endif // AUTO_MEM_H 