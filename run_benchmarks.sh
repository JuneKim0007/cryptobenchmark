# !/bin/bash

INPUT_SIZES=(256 512 1024) # 256 160 1024 118724  4086 81920
N_TIMES=100  #times each algo is repeated (size of input list)
N_TEST_TIMES=2 # times each test case is repeated (N) in  _N_ * (size of input list)
SLEEP_TIME=1

PROVIDERS=(AndroidOpenSSL BC AndroidKeyStoreBCWorkaround AndroidKeyStore )

MAC_KEY_LEN=(8 16 32 64 )

SYM_ALGOS=( AES CHACHA20 BLOWFISH ARC4 DES 3DES )
SYM_MODES=( ECB ) # CBC CTR GCM OFB GCM-SIV )
SYM_PADD=( NoPadding PKCS5PADDING PKCS7PADDING )
SYM_KEY_LEN=(40 56 128 168 192 256)

ASSYM_PROVIDERS=(AndroidOpenSSL AndroidKeyStoreBCWorkaround BC)
ASSYM_INPUT_SIZES=(116 244 372)
ASSYM_ALGOS=( RSA )
ASSYM_MODES=( ECB )
ASSYM_PADDS=( NOPADDING OAEPPADDING OAEPWITHSHA-1ANDMGF1PADDING OAEPWITHSHA-224ANDMGF1PADDING OAEPWITHSHA-256ANDMGF1PADDING OAEPWITHSHA-384ANDMGF1PADDING OAEPWITHSHA-512ANDMGF1PADDING)
ASSYM_KEYSPEC=( 0 1 )
ASSYM_KEY_LEN=(1024 2048 4096)

SIGN_KEY_LEN=(1024 2048 4096)
SIGN_ALGOS=(RSA DSA) # necessary for keygen
#SIGN_PADDS=( NOPADDING )
SIGN_PROVIDERS=(AndroidOpenSSL AndroidKeyStoreBCWorkaround BC)


function testDigest(){
    INPUT_SIZES=(512 1024 2048)
    # Digest (no need to specify algorithm)
    for is in ${INPUT_SIZES[@]}; do
        python3 benchmark.py -u -c MeasureDigestTest -nt $N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME -is  $is -a ""
    done
}

function testMAC(){
    # HMAC (no need to specify algorithm)
    for is in ${INPUT_SIZES[@]}; do
        #for pv in ${PROVIDERS[@]}; do
            for keylen in  ${MAC_KEY_LEN[@]}; do
                python3 benchmark.py -u -c MeasureHMACTest -nt $N_TIMES --n_test_times $N_TEST_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  s $is -kl "" -pv "" -a ""
            done
        #done
    done
}

function testSign(){
    for algo in ${SIGN_ALGOS[@]}; do
        for pv in ${SIGN_PROVIDERS[@]}; do
            for is in ${INPUT_SIZES[@]}; do
                for keylen in  ${SIGN_KEY_LEN[@]}; do
                    python3 benchmark.py    -u -c MeasureSignTest -nt $N_TIMES --n_test_times $N_TEST_TIMES   -s $SLEEP_TIME  -is $is -kl $keylen  -a $algo -pv $pv -pd "" -m ""
                done
            done
        done
    done
}


function testSignAndVerify(){
    for algo in ${SIGN_ALGOS[@]}; do
        for pv in ${PROVIDERS[@]}; do
            for is in ${INPUT_SIZES[@]}; do
                for keylen in  ${SIGN_KEY_LEN[@]}; do
                    python3 benchmark.py    -u -c MeasureSignVerifyTest -nt $N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME  -is $is -kl $keylen -a $algo -pv $pv  -pd "" -m ""
                done
            done
        done
    done
}


function testSymEncrypt(){
    for algo in ${SYM_ALGOS[@]}; do
        for pv in ${PROVIDERS[@]}; do
            for is in ${INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    if [ $algo == "AES" ] || [ $algo == "3DES" ]; then
                        for mode in  ${SYM_MODES[@]}; do
                            for pad in  ${SYM_PADD[@]}; do
                                python3 benchmark.py    -u -c MeasureSymmetricEncryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -kl $keylen -a $algo -pd $pad -m $mode  
                            done
                        done
                    else
                        python3 benchmark.py    -u -c MeasureSymmetricEncryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -pd "" -m "" -kl $keylen -a $algo  
                    fi
                done
            done
        done
    done
}

function testSymDecrypt(){
    for algo in ${SYM_ALGOS[@]}; do
        for pv in ${PROVIDERS[@]}; do
            for is in ${INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    if [ $algo == "AES" ] || [ $algo == "3DES" ]; then
                        for mode in  ${SYM_MODES[@]}; do
                            for pad in  ${SYM_PADD[@]}; do
                                python3 benchmark.py    -u -c MeasureSymmetricEncryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME  -is $is -kl $keylen -a $algo -pd $pad -m $mode  
                            done
                        done
                    else
                        python3 benchmark.py    -u -c MeasureSymmetricDecryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -pd "" -m "" -kl $keylen -a $algo  
                    fi
                done
            done
        done
    done
}

function testSymKeyGen(){
    for algo in ${SYM_ALGOS[@]}; do
        #for pv in ${PROVIDERS[@]}; do
            for is in ${INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    #for mode in  ${SYM_MODES[@]}; do
                        #for pad in  ${SYM_PADD[@]}; do
                            python3 benchmark.py   -u -c MeasureSymmetricKeygenTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is  -kl $keylen   
                        #done
                    #done
                done
            done
        #done
    done
}


function testSymm(){
    #for algo in ${SYM_ALGOS[@]}; do
        for pv in ${PROVIDERS[@]}; do
            for is in ${INPUT_SIZES[@]}; do
                for keylen in  ${SYM_KEY_LEN[@]}; do
                    #for mode in  ${SYM_MODES[@]}; do
                        #for pad in  ${SYM_PADD[@]}; do
                            python3 benchmark.py -u -c MeasureSymmetricEncryptDecryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES -s $SLEEP_TIME -is $is  -kl $keylen   
                        #done
                    #done
                done
            done
        done
    #done
}


# ASSYM

function testAssymmKeygen(){
    #for pv in ${PROVIDERS[@]}; do
        for keylen in  ${ASSYM_KEY_LEN[@]}; do
            #for pad in  ${ASSYM_PADDS[@]}; do  
                for kpad in  ${ASSYM_KEYSPEC[@]}; do
                    python3 benchmark.py -u -c MeasureAssymmetricEncryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is  
                done
            #done
        done
    #done
}

function testAssymmEncrypt(){
    #for pv in ${ASSYM_PROVIDERS[@]}; do
        for is in ${ASSYM_INPUT_SIZES[@]}; do
            for keylen in  ${ASSYM_KEY_LEN[@]}; do
                #for pad in  ${ASSYM_PADDS[@]}; do  
                #    for kpad in  ${ASSYM_KEYSPEC[@]}; do
                        python3 benchmark.py -u -c MeasureAssymmetricEncryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -ks $kpad -kl $keylen  
                #    done
                #done
            done
        done
    #done
}

function testAssymmDecrypt(){
    #for pv in ${ASSYM_PROVIDERS[@]}; do
        for is in ${ASSYM_INPUT_SIZES[@]}; do
            #for pad in  ${ASSYM_PADDS[@]}; do
                for keylen in  ${ASSYM_KEY_LEN[@]}; do
                    for kpad in  ${ASSYM_KEYSPEC[@]}; do
                        python3 benchmark.py  -u -c MeasureAssymmetricDecryptTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -ks $kpad -kl $keylen 
                    done
                done
            #done
        done
    #done
}


function testAssymm(){
    #for pv in ${PROVIDERS[@]}; do
        for is in ${ASSYM_INPUT_SIZES[@]}; do
            #for pad in  ${ASSYM_PADDS[@]}; do
                for keylen in  ${ASSYM_KEY_LEN[@]}; do
                    for kpad in  ${ASSYM_KEYSPEC[@]}; do
                        python3 benchmark.py -u -c MeasureAssymmetricAllTest -nt $N_TIMES --n_test_times $N_TEST_TIMES  -s $SLEEP_TIME -is $is -ks $kpad -kl $keylen 
                    done
                done
            #done
        done
    #done
}


# digest
testDigest

# hmac test
#testMAC

# test sign
#testSign

#testSymEncrypt

#testAssymmEncrypt

#testSignAndVerify

x='''
testSymEncrypt

testSymDecrypt

testSymKeyGen

testSymm

testAssymmEncrypt

testAssymmDecrypt

testAssymm'''



