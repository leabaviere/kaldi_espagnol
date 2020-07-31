#!/bin/bash
. ./path.sh || echo "NOPE"
. ./cmd.sh
nj=11
lm_order=3
echo
echo "===== LANGUAGE MODEL CREATION ====="
echo "===== MAKING lm.arpa ====="
echo
loc=`which ngram-count`;
if [ -z $loc ]; then
        if uname -a | grep 64 >/dev/null; then
                sdir=$KALDI_ROOT/tools/srilm/bin/i686-m64
        else
                        sdir=$KALDI_ROOT/tools/srilm/bin/i686
        fi
        if [ -f $sdir/ngram-count ]; then
                        echo "Using SRILM language modelling tool from $sdir"
                        export PATH=$PATH:$sdir
        else
                        echo "SRILM toolkit is probably not installed.
                                Instructions: tools/install_srilm.sh"
                        echo "NOPE"
        fi
fi
local=data/local
mkdir $local/tmp
ngram-count -prune 1e-7.5 -order $lm_order -vocab $local/tmp/most_frequent_words.txt -kndiscount -text $local/corpus_30Go.txt -lm $local/tmp/lm_1e75.arpa
echo
echo "===== MAKING G.fst ====="
echo
lang=data/lang
arpa2fst --disambig-symbol=#0 --read-symbol-table=$lang/words.txt $local/tmp/lm_1e75.arpa $lang/G.fst


echo
echo "===== GRAPHS AND DECODING ====="
echo
utils/mkgraph.sh data/lang exp/tri5a_train exp/tri5a_train/graph
utils/mkgraph.sh data/lang exp/sgmm5_train exp/sgmm5_train/graph
 
steps/decode_fmllr_extra.sh --nj $nj --cmd "$decode_cmd" --num-threads 4 --parallel-opts " -pe smp 4" \
  --config conf/decode.config  --scoring-opts "--min-lmwt 8 --max-lmwt 12"\
 exp/tri5a_train/graph data/dev exp/tri5a_train/decode_dev
steps/decode_sgmm2.sh --nj $nj --cmd "$decode_cmd" --num-threads 5 \
  --config conf/decode.config  --scoring-opts "--min-lmwt 8 --max-lmwt 16" --transform-dir exp/tri5a_train/decode_dev \
 exp/sgmm5_train/graph data/dev exp/sgmm5_train/decode_dev
for iter in 1 2 3 4; do
  decode=exp/sgmm5_mmi_b0.1_train/decode_dev_it$iter
  mkdir -p $decode
  steps/decode_sgmm2_rescore.sh  \
    --cmd "$decode_cmd" --iter $iter --transform-dir exp/tri5a_train/decode_dev \
    data/lang data/dev/  exp/sgmm5_train/decode_dev $decode
done

steps/decode_fmllr_extra.sh --nj $nj --cmd "$decode_cmd" --num-threads 4 --parallel-opts " -pe smp 4" \
  --config conf/decode.config  --scoring-opts "--min-lmwt 8 --max-lmwt 12"\
 exp/tri5a_train/graph data/test exp/tri5a_train/decode_test
steps/decode_sgmm2.sh --nj $nj --cmd "$decode_cmd" --num-threads 5 \
  --config conf/decode.config  --scoring-opts "--min-lmwt 8 --max-lmwt 16" --transform-dir exp/tri5a_train/decode_test \
 exp/sgmm5_train/graph data/test exp/sgmm5_train/decode_test
for iter in 1 2 3 4; do
  decode=exp/sgmm5_mmi_b0.1_train/decode_test_it$iter
  mkdir -p $decode
  steps/decode_sgmm2_rescore.sh  \
    --cmd "$decode_cmd" --iter $iter --transform-dir exp/tri5a_train/decode_test \
    data/lang data/test/  exp/sgmm5_train/decode_test $decode
done
echo
echo "===== run.sh is finished ====="
echo
