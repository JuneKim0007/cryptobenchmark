// Pins the calling thread to one core; an unrooted app may restrict its own threads, not isolate a core.
#define _GNU_SOURCE
#include <errno.h>
#include <jni.h>
#include <sched.h>

JNIEXPORT jint JNICALL Java_io_github_junekim0007_cryptobench_Affinity_pin(JNIEnv *env, jobject self, jint core) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(core, &set);
    return sched_setaffinity(0, sizeof(set), &set) == 0 ? 0 : errno;
}

JNIEXPORT jlong JNICALL Java_io_github_junekim0007_cryptobench_Affinity_allowed(JNIEnv *env, jobject self) {
    cpu_set_t set;
    CPU_ZERO(&set);
    if (sched_getaffinity(0, sizeof(set), &set) != 0) return -1;
    jlong mask = 0;
    for (int core = 0; core < 64; core++) if (CPU_ISSET(core, &set)) mask |= (1LL << core);
    return mask;
}

JNIEXPORT jint JNICALL Java_io_github_junekim0007_cryptobench_Affinity_current(JNIEnv *env, jobject self) {
    return sched_getcpu();
}

JNIEXPORT jint JNICALL Java_io_github_junekim0007_cryptobench_Affinity_restore(JNIEnv *env, jobject self, jlong mask) {
    cpu_set_t set;
    CPU_ZERO(&set);
    for (int core = 0; core < 64; core++) if (mask & (1LL << core)) CPU_SET(core, &set);
    return sched_setaffinity(0, sizeof(set), &set) == 0 ? 0 : errno;
}
