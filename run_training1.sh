#!/bin/bash
. ./path.sh || echo "NOPE"
. ./cmd.sh || echo "NOPE"
nj=11      
lm_order=3 # language model order 
. utils/parse_options.sh || echo "NOPE"
[[ $# -ge 1 ]] && { echo "Wrong arguments!"; echo "NOPE"; }
# Removing previously created data (from last run.sh execution)
#rm -rf exp mfcc data/train/spk2utt data/train/cmvn.scp data/train/feats.scp data/train/split1 data/test/spk2utt data/test/cmvn.scp data/test/feats.scp data/test/split1 data/local/lang data/lang data/local/tmp data/local/dict/lexiconp.txt
echo
echo "===== PREPARING ACOUSTIC DATA ====="
echo
# Making spk2utt files
utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
utils/utt2spk_to_spk2utt.pl data/dev/utt2spk > data/dev/spk2utt
echo
echo "===== FEATURES EXTRACTION ====="
echo
# Making feats.scp files
mfccdir=mfcc
utils/fix_data_dir.sh data/train 
utils/fix_data_dir.sh data/test
utils/fix_data_dir.sh data/dev
steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/train exp/make_mfcc/train $mfccdir
steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/test exp/make_mfcc/test $mfccdir
steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/dev exp/make_mfcc/dev $mfccdir
utils/validate_data_dir.sh data/train
utils/validate_data_dir.sh data/test
utils/validate_data_dir.sh data/dev
# Making cmvn.scp files
steps/compute_cmvn_stats.sh data/train exp/make_mfcc/train $mfccdir
steps/compute_cmvn_stats.sh data/test exp/make_mfcc/test $mfccdir
steps/compute_cmvn_stats.sh data/dev exp/make_mfcc/dev $mfccdir
echo
echo "===== PREPARING LANGUAGE DATA ====="
echo
utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang
echo
echo "===== MONO TRAINING ====="
echo
steps/train_mono.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono_subset_train  || echo "NOPE"
echo
echo "===== MONO ALIGNMENT ====="
echo
steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono_subset_train exp/mono_ali_subset_train || echo "NOPE"
echo
echo "===== TRI1 TRAINING ====="
echo
steps/train_deltas.sh --cmd "$train_cmd" 2500 20000 data/train data/lang exp/mono_ali_subset_train exp/tri1_subset_train || echo "NOPE"
echo
echo "===== TRI1 ALIGNMENT ====="
echo
steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri1_subset_train exp/tri1_ali_subset_train || echo "NOPE"
echo
echo "===== TRI2 TRAINING ====="
echo
steps/train_deltas.sh --cmd "$train_cmd" 2500 20000 data/train data/lang exp/tri1_ali_subset_train exp/tri2_subset_train || echo "NOPE"
echo 
echo "===== TRI2 ALIGNMENT ====="
echo
steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri2_subset_train exp/tri2_ali_subset_train || echo "NOPE"
echo
echo "===== TRI3A TRAINING ====="
echo
steps/train_lda_mllt.sh --cmd "$train_cmd" --splice-opts "--left-context=3 --right-context=3" \
   3000 40000 data/train data/lang exp/tri2_ali_subset_train exp/tri3a_subset_train || echo "NOPE"
echo
echo "===== TRI3A ALIGNMENT ====="
echo
steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri3a_subset_train exp/tri3a_ali_subset_train || echo "NOPE"
echo
echo "===== TRI4A TRAINING ====="
echo
steps/train_sat.sh --cmd "$train_cmd" 4000 60000 data/train data/lang exp/tri3a_ali_subset_train  exp/tri4a_subset_train || echo "NOPE"
echo
echo "===== TRI4A ALIGNMENT ====="
echo
steps/align_fmllr.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri4a_subset_train exp/tri4a_ali_subset_train || echo "NOPE"
echo 
echo "===== TRI5A TRAINING (Reducing number of gaussians) ====="
echo
steps/train_sat.sh --cmd "$train_cmd" 5000 120000 data/train data/lang exp/tri4a_ali_subset_train exp/tri5a_subset_train || echo "NOPE"
echo
echo "===== TRI5A ALIGNMENT ====="
echo
steps/align_fmllr.sh --boost-silence 0.5 --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri5a_subset_train exp/tri5a_ali_subset_train || echo "NOPE"
echo
echo "===== UBM5 TRAINING ====="
echo
steps/train_ubm.sh --cmd "$train_cmd" 750 data/train data/lang exp/tri5a_ali_subset_train exp/ubm5_subset_train || echo "NOPE"
echo
echo "===== SGMM2 TRAINING ====="
echo
steps/train_sgmm2.sh --cmd "$train_cmd" 5000 18000 data/train data/lang exp/tri5a_ali_subset_train exp/ubm5_subset_train/final.ubm exp/sgmm5_subset_train || echo "NOPE"
echo 
echo "===== SGMM2 ALIGNMENT ====="
echo
steps/align_sgmm2.sh --nj $nj  --cmd "$train_cmd" --transform-dir exp/tri5a_ali_subset_train --use-graphs true --use-gselect true \
  data/train data/lang exp/sgmm5_subset_train exp/sgmm5_ali_subset_train
echo 
echo "===== MAKE DENLATS ====="
echo
steps/make_denlats_sgmm2.sh --nj $nj --sub-split 32 --num-threads 4 \
  --beam 10.0 --lattice-beam 6 --cmd "$decode_cmd" --transform-dir exp/tri5a_ali_subset_train \
  data/train data/lang exp/sgmm5_ali_subset_train exp/sgmm5_denlats_subset_train
echo
echo "===== MMI SGMM2 TRAINING ====="
echo
steps/train_mmi_sgmm2.sh \
  --cmd "$train_cmd" --drop-frames true --transform-dir exp/tri5a_ali_subset_train --boost 0.1 \
  data/train data/lang exp/sgmm5_ali_subset_train exp/sgmm5_denlats_subset_train \
  exp/sgmm5_mmi_b0.1_subset_train
