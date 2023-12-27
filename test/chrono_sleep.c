void chrono_sleep(uint64_t t) {
	long t2 = (long)t;
	StdTimespec ts = {
		.tv_sec = t2 / e9,
		.tv_nsec = t2 % e9,
	};
	nanosleep(&ts, 0);
}
