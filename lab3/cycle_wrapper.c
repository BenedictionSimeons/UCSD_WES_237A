// Benediction Bora
#include "cycletime.h"

//Initialize PMU counters
void init_counter(int32_t do_reset, int32_t enable_divider) {
     init_counters(do_reset, enable_divider);
}

//Get cycle count
unsigned int get_cycle_count() {
    return get_cyclecount();
}

