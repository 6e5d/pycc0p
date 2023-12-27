int main(void) {
	for (int i = 0;; i += 1) {
		if(i == 5) {
			continue;
		}
		if(i >= 5) {
			break;
		}
	}
	return 0;
}
