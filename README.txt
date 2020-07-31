Kaldi scripts
	cmd.sh et path.sh sont les fichiers pour l'initialisation du modèle
	run_training1.sh est le training script pour le modèle kaldi 
	run_decoding1.sh sert à la création des graphs et à l'exécution de la phase décodage du modèle

Le script "script_pipelines.py' est le script ayant permis le nettoyage des textes pour l'obtention d'un corpus \
    pour le modèle de language, est inspiré de celui du modèle français et adapté pour l'espagnol.


DOSSIER KALDI : 

/media/storage0/ilyes/kaldi/egs/Espagnol/cv_espagnol/

	data/dev/ --> contient les fichiers utt2spk spk2gender text wav.scp pour les données dev 
	data/test/ --> contient les fichiers utt2spk spk2gender text wav.scp pour les données test	
	data/train/ --> contient les fichiers utt2spk spk2gender text wav.scp pour les données train
	data/lang/ --> contient les fichiers G.fst et L.fst 
	data/local/ --> contient les différents corpus pour le modèle de langage
	data/local/dict/ --> contient le fichier lexicon.txt
	data/local/tmp/ --> contient les fichiers lm.arpa (utilisé : lm_1e7.arpa) et le vocabulaire most_frequent_words.txt

	dev/ --> contient les fichiers audios dev

	test/ --> contient les fichiers audios test

	train/ --> contient les fichiers audios train

	exp/make_mfcc --> contient les fichiers mfcc
	exp/previous_runs --> contient les fichiers exp des anciens entraînements (ainsi que les scripts \
	            correspondants pour les run_subset1,2,3...)
	exp/* --> les dossiers d'entraînements du modèle actuel 
		mono : entraînement monophone (train_mono.sh)
		mono_ali : alignement monophone (align_si.sh)
		tri1 : 1er entraînement triphone (paramètres 2000 10000 avec boost-silence 1.25 - train_deltas.sh)
		tri1_ali : alignement du premier triphone (align_si.sh)
		tri2 : 2e entraînement triphone (paramètres 2000 10000 - train_deltas.sh)
		tri2_ali : alignement du deuxième triphone (align_si.sh)
		tri3a : 3e entraînement triphone (paramètres 2500 15000 - train_lda_mllt.sh)
		tri3a_ali : alignement du troisième triphone (align_si.sh)
		tri4a : 4e entraînement triphone (paramètres 2500 15000 - train_sat.sh)
		tri4a_ali : alignement du quatrième triphone (align_fmllr.sh)
		tri5a : 5e entraînement triphone (paramètres 4200 40000 - train_sat.sh)
		tri5a_ali : alignement du cinquième triphone (align_fmllr.sh)
		ubm5 : entraînement ubm5 (paramètre 750 train_ubm.sh)
		sgmm5 : entraînement sgmm2 (paramètres 5000 18000 - train_sgmm2.sh)
		sgmm5_ali : alignement du sgmm2 (align_sgmm2.sh)
		sgmm5_denlats : denlats (make_denlats_sgmm2.sh)
		sgmm5_mmi_b0.1 : entraînement MMI sgmm2 (train_mmi_sgmm2.sh)
	exp/tri5a/graph --> graph HCLG.fst
	exp/sgmm5/graph --> graph HCLG.fst

	run_training1.sh --> script utilisé pour la préparation des données et les différents entraînements du modèle

	run_decoding1.sh --> script pour la création du modèle de langage et des graphs ainsi que pour le 
	        \décodage des données dev et test



Corpus audios utilisés : 
	126.601 audios d'environ 5 secondes (soit 167h au total) de CommonVoice https://voice.mozilla.org/fr/datasets
	59.297 audios d'environ 5 secondes (soit 108h au total) de Caito https://www.caito.de/2019/01/the-m-ailabs-speech-dataset/
	35.860 audios d'environ 5 secondes (soit 62h au total) de OpenSLR Librispeech http://www.openslr.org/resources.php
	980 audios d'environ 5 secondes (soit 1h30 au total) de VoxForge http://www.voxforge.org/es/Downloads	

Corpus écrits utilisés : /media/storage0/ilyes/kaldi/egs/Espagnol/cv_espagnol/data/local/corpus_30Go.txt contient : 
	57 fichiers de 1.831.518 mots chacun : "120-million-word-spanish-corpus" https://www.kaggle.com/rtatman/120-million-word-spanish-corpus
	7034 fichiers de 200 mots chacun : "TEI_ES" 
	18 fichiers de 112.151 mots chacun : "gutenberg" https://www.gutenberg.org/browse/languages/es
	61 fichiers de 84.417.114 mots chacun : "open_subtitles" http://opus.nlpl.eu/OpenSubtitles.php
	100 fichiers de 8.037.810 mots chacun : "spanish_billion_words" https://crscardellino.github.io/SBWCE/
	1 fichier de 11.220.790 mots : "corpus_coca" 
	

Au final, j'ai donc entraîner mon modèle avec le script run_training1.sh, et utilisé comme modèle de langage \
        le corpus_30Go.txt et le vocabulaire most_frequent_words.txt, et enfin fait la création des graphs et \
        le décodage avec le script run_decoding1.sh

Les résultats finaux que j'ai pu observé sont les suivants : En entraînant avec 216.000 audios, et en utilisant \ 
        12.600 audios pour la vérification et 12.600 pour le décodage, on a pu obtenir un WER d'approximativement \
        20%, en utilisant un modèle Hmm-Gmm.
