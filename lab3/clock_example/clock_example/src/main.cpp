//
//  main.cpp
//  Lab4
//
//  Created by Alireza on 2/14/20.
//  Copyright Â© 2020 Alireza. All rights reserved.
//

#include "main.h"
#include "cycletime.h"
#include "timer.h"
#include <unistd.h>

using namespace std;

int main(int argc, const char * argv[])
{
	float cpu_timer;
	unsigned int delay = 1;
	
	cout << "\nWES237A lab 4" << endl;

	char key=0;
	
	// 1 argument on command line: delay = arg
	if(argc >= 2)
	{
		delay = atoi(argv[1]);
	}

    //TODO: declare 2 cpu_count variables: 1 for before sleeping, 1 for after sleeping (see cpu_timer)
	unsigned int cpu_count1;
	unsigned int cpu_count2;
    //TODO: initialize the counter
	init_counters(0,0);
	
    //TODO: get the cyclecount before sleeping
	//asm volatile ("MRC p15, 0, %0, c9, c13, 0\n\t" : "=r"(cpu_count1));
	cpu_count1 = get_cyclecount();

    usleep(delay);
    //TODO: get the cyclecount after sleeping
	cpu_count2 = get_cyclecount();
	//asm volatile ("MRC p15, 0, %0, c9, c13, 0\n\t" : "=r"(cpu_count2));

    //TODO: subtract the before and after cyclecount
	int32_t diff = cpu_count2 - cpu_count1;
    //TODO: print the cycle count (see the print statement for the cpu_timer below)

	cout << "CPU counter #1: "<< cpu_count1/1000000000.0 << endl;

	cout << "CPU counter #2: "<< cpu_count2/1000000000.0 << endl;

	cout << "Cycle count diff after sleep: "<< (double)diff/1000000000.0 << endl;

	LinuxTimer t;
	usleep(delay);
	t.stop();
	cpu_timer = t.getElapsed();

	
	cout << "Timer: " << (double)cpu_timer/1000000000.0 << endl;
	cout<<"\n"<<endl;
	return 0;
}

