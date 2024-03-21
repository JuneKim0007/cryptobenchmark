# !/bin/bash

INPUT_SIZES=(256 512 1024 2048) # 256 160 1024 118724  4086 81920
N_TIMES=10000  #times each algo is repeated (size of input list)
N_TEST_TIMES=30 # times each test case is repeated (N) in  _N_ * (size of input list)
SLEEP_TIME=2 # time to sleep between each test case

PROVIDERS=(AndroidOpenSSL BC AndroidKeyStoreBCWorkaround AndroidKeyStore )

MAC_N_TIMES=10
MAC_KEY_LEN=(8 16 32 64)
SYM_INPUT_SIZES=(32 128 256)
SYM_ALGOS=( AES DES CHACHA20 BLOWFISH ARC4 DES 3DES )
#SYM_MODES=( ECB CBC CTR GCM OFB GCM-SIV CFB)
SYM_PADD=( NoPadding PKCS5PADDING PKCS7PADDING )
SYM_KEY_LEN=(40 56 128 168 192 256)
SYM_N_TIMES=1000
SYM_PROVIDERS=(AndroidOpenSSL BC AndroidKeyStoreBCWorkaround)

ASSYM_PROVIDERS=(AndroidOpenSSL AndroidKeyStoreBCWorkaround BC)
ASSYM_INPUT_SIZES=(116 244 372)
ASSYM_ALGOS=( RSA )
ASSYM_MODES=( ECB )
ASSYM_PADDS=(NOPADDING OAEPPADDING OAEPWITHSHA-1ANDMGF1PADDING OAEPWITHSHA-224ANDMGF1PADDING OAEPWITHSHA-256ANDMGF1PADDING OAEPWITHSHA-384ANDMGF1PADDING OAEPWITHSHA-512ANDMGF1PADDING)
ASSYM_KEYSPEC=( 0 1 )
ASSYM_KEY_LEN=(1024 2048 4096)
ASSYM_N_TIMES=25

SIGN_INPUT_SIZES=( 64 )
SIGN_KEY_LEN=( 1024 2048 4096)
SIGN_ALGOS=(RSA DSA) # necessary for keygen
#SIGN_PADDS=( NOPADDING )
SIGN_PROVIDERS=(AndroidOpenSSL AndroidKeyStoreBCWorkaround) # BC)
SIGN_N_TIMES=100


function testDigest(){
    # Digest (no need to specify algorithm)
    for is in ${INPUT_SIZES[@]}; do
        python3 benchmark.py -c MeasureDigestTest -nt $N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME -is  $is -a ""
    done
}

function testMAC(){
    # HMAC (no need to specify algorithm)
    for is in ${INPUT_SIZES[@]}; do
        #for pv in ${PROVIDERS[@]}; do # assuming that all providers have the same default provider (TODO confirm)
            for keylen in  ${MAC_KEY_LEN[@]}; do
                python3 benchmark.py -c MeasureHMACTest -nt $MAC_N_TIMES --n_test_times $N_TEST_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -kl $keylen -pv "" -a ""
            done
        #done
    done
}

function testSign(){
    for algo in ${SIGN_ALGOS[@]}; do
        for pv in ${SIGN_PROVIDERS[@]}; do
            for is in ${SIGN_INPUT_SIZES[@]}; do
                for keylen in  ${SIGN_KEY_LEN[@]}; do
                    python3 benchmark.py -c MeasureSignTest -nt $SIGN_N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME  -is $is -kl $keylen  -a $algo -pv $pv -pd "" -m ""
                done
            done
        done
    done
}


function testSignAndVerify(){
    for algo in ${SIGN_ALGOS[@]}; do
        for pv in ${SIGN_PROVIDERS[@]}; do
            for is in ${SIGN_INPUT_SIZES[@]}; do
                for keylen in  ${SIGN_KEY_LEN[@]}; do
                    python3 benchmark.py -c MeasureSignVerifyTest -nt $SIGN_N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME  -is $is -kl $keylen -a $algo -pv $pv  -pd "" -m ""
                done
            done
        done
    done
}


function testSymEncrypt(){
    # we need to specify more things since some parameters affect the keygen process
    for algo in ${SYM_ALGOS[@]}; do
        for pv in ${SYM_PROVIDERS[@]}; do
            for is in ${SYM_INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    #if [ $algo == "AES" ] || [ $algo == "3DES" ]; then
                    #    for mode in  ${SYM_MODES[@]}; do
                    #        for pad in  ${SYM_PADD[@]}; do
                    #            python3 benchmark.py -c MeasureSymmetricEncryptTest -nt $SYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -kl $keylen -a $algo -pd $pad -m $mode  
                    #        done
                    #    done
                    #else
                    python3 benchmark.py -c MeasureSymmetricEncryptTest -nt $SYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -pd "" -m "" -kl $keylen -a $algo
                    #fi
                done
            done
        done
    done
}

function testSymDecrypt(){
    for algo in ${SYM_ALGOS[@]}; do
        for pv in ${SYM_PROVIDERS[@]}; do
            for is in ${SYM_INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    #if [ $algo == "AES" ] || [ $algo == "3DES" ]; then
                    #    for mode in  ${SYM_MODES[@]}; do
                    #        for pad in  ${SYM_PADD[@]}; do
                    #            python3 benchmark.py -c MeasureSymmetricEncryptTest -nt $SYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -kl $keylen -a $algo -pd $pad -m $mode  
                    #        done
                    #    done
                    #else
                    python3 benchmark.py -c MeasureSymmetricDecryptTest -nt $SYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -pd "" -m "" -kl $keylen -a $algo  
                    #fi
                done
            done
        done
    done
}

function testSymKeyGen(){
    for is in ${SYM_INPUT_SIZES[@]}; do
        for keylen in  ${SYM_KEY_LEN[@]}; do
            python3 benchmark.py -c MeasureSymmetricKeygenTest -nt $SYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is  -kl $keylen   
        done
    done
}


function testSymm(){
    for algo in ${SYM_ALGOS[@]}; do
        for pv in ${SYM_PROVIDERS[@]}; do
            for is in ${SYM_INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    #for mode in  ${SYM_MODES[@]}; do
                    #    for pad in  ${SYM_PADD[@]}; do
                    python3 benchmark.py-c MeasureSymmetricEncryptDecryptTest -nt $SYM_N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME -is $is  -kl $keylen   
                    #    done
                    #done
                done
            done
        done
    done
}


# ASSYM

function testAssymmKeygen(){
    #for pv in ${PROVIDERS[@]}; do
        for keylen in  ${ASSYM_KEY_LEN[@]}; do
            #for pad in  ${ASSYM_PADDS[@]}; do  
                for kpad in  ${ASSYM_KEYSPEC[@]}; do
                    python3 benchmark.py-c MeasureAssymmetricEncryptTest -nt $ASSYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is  
                done
            #done
        done
    #done
}

function testAssymmEncrypt(){
    for pv in ${ASSYM_PROVIDERS[@]}; do
        for is in ${ASSYM_INPUT_SIZES[@]}; do
            for keylen in  ${ASSYM_KEY_LEN[@]}; do
                #for pad in  ${ASSYM_PADDS[@]}; do  
                #    for kpad in  ${ASSYM_KEYSPEC[@]}; do
                        python3 benchmark.py -c MeasureAssymmetricEncryptTest -nt $ASSYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is  -kl $keylen  
                #    done
                #done
            done
        done
    done
}

function testAssymmDecrypt(){
    for pv in ${ASSYM_PROVIDERS[@]}; do
        for is in ${ASSYM_INPUT_SIZES[@]}; do
            #for pad in  ${ASSYM_PADDS[@]}; do
                for keylen in  ${ASSYM_KEY_LEN[@]}; do
                    for kpad in  ${ASSYM_KEYSPEC[@]}; do
                        python3 benchmark.py -c MeasureAssymmetricDecryptTest -nt $ASSYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -ks $kpad -kl $keylen 
                    done
                done
            #done
        done
    done
}


function testAssymm(){
    for pv in ${ASSYM_PROVIDERS[@]}; do
        for is in ${ASSYM_INPUT_SIZES[@]}; do
            #for pad in  ${ASSYM_PADDS[@]}; do
                for keylen in  ${ASSYM_KEY_LEN[@]}; do
                    for kpad in  ${ASSYM_KEYSPEC[@]}; do
                        python3 benchmark.py -c MeasureAssymmetricAllTest -nt $ASSYM_N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -ks $kpad -kl $keylen 
                    done
                done
            #done
        done
    done
}


# digest
testDigest

# hmac test
testMAC

# test sign
testSign

testSignAndVerify

testSymEncrypt

testSymm

testAssymmEncrypt

testSignAndVerify

x='''
testSymEncrypt

testSymDecrypt

testSymKeyGen

testSymm

testAssymmEncrypt

testAssymmDecrypt

testAssymm'''



