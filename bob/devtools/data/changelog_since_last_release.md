* bob.buildout
  * patch
     - bob.buildout!30 Update guide.rst for automated environment creation
* bob.extension
  * v3.0.0 (Jun 27, 2018 13:53)
     - Breaking and significant changes:
     - Removed bob_new_version script bob.extension!76
     - Implemented `bob` click command bob.extension!64 bob.extension!73
       bob.extension!77 bob.extension!74 bob.extension!75
     - Detailed changes:
     - bob.extension!75 Fix a bug when commands where invoked multiple times
     - bob.extension!72 Added the function bob.extension.download_and_unzip in
       the core functionalities: Closes bob.extension#50
     - bob.extension!77 Fix list option
     - bob.extension!64 Implementation of the bob script using click: Fixes
       bob.extension#44
     - bob.extension!79 added support for pytorch doc
     - bob.extension!80 Add scikit-learn intersphinx mapping
     - bob.extension!81 Add prefix aliasing for bob commands
     - bob.extension!83 Fixed issue with bz2 files: For some reason, it is not
       possible to open some `bz2` files for reading ('r:bz2') using the
       `tarfile` module.  For instance, this is failing with the `dlib`
       landmarks model.  If I use the `bz2` module it works.    This patch uses
       the `bz2` module for `bz2` compressed files.
     - bob.extension!82 Resolve "The `-DBOOST_VERSION` flag has unnecessary and
       unwanted quotes": Closes bob.extension#58
     - bob.extension!76 Resolve "Documentation should be improved": [doc] added
       the reference to NumPy style docstrings, added note on new package
       instructions, added corresponding links    Closes bob.extension#55
  * minor
     - Improved the help option on all Bob click commands !84
     - Improved the click bool option !85
     - Added functionality to dump config file when calling a ConfigCommand !86
     - Add an ignore variable to log_parameters function (click helper) !88
     - bob.extension!87 Add a common_attribute argument to config.load: Fixes
       bob.extension#64
* bob.blitz
  * patch
     - bob.blitz!11 [sphinx] Fixed doctest: Close bob.blitz#12
* bob.core
  * patch
     - bob.core!17 Adapted the documentation to the new behavior of version
       exporting: When merging bob.extension!82, this MR will update the
       according documentation.
     - bob.core!16 Use log modules from bob.extension
* bob.io.base
  * patch
     - bob.io.base!25 Resolve "HDF5_VERSION is computed but never used": Closes
       bob.io.base#19
* bob.math
  * patch
     - bob.math!18 Fixing SVD test: Just fixing the sign of the last
       eigenvector.    More info check it out bob.math#10
* bob.measure
  * major
     - Breaking and significant changes:
     - Removed the old plotting scripts (``compute_perf.py``, etc.).
     - Added a new 2-column score format specific to bob.measure.
     - Implemented generic metrics and plotting scripts. Do ``bob measure
       --help`` to see the new scripts and refer to the documentation.
     - Matplotlib 2.2 and above is required now.
     - Some biometric-related-only functionality is moved to bob.bio.base.
     - Detailed changes:
     - bob.measure!52 generic plotting script for bob measure: From
       bob.measure#37, provide generic plotting scripts:  *  bob measure
       evaluate  *  bob measure hist  *  bob measure hter  *  ...
     - bob.measure!55 Change option name criter to criterion
     - bob.measure!56 Fix error in context name
     - bob.measure!57 Extend bins number option
     - bob.measure!58 Change variable name form criter to criterion
     - bob.measure!59 Bug fix: incorrect input file reading
     - bob.measure!60 Bugfix
     - bob.measure!54 Refactors the score loading and scripts functionality:
       This merge request:    *  Move the biometric related functionality of
       bob.measure to bob.bio.base.  *  Add confidence interval calculations  *
       Provide a score format for bob.measure with load functionalities  *
       Provide a generic plotting script bob measure in bob.measure using
       bob.measure input file format:       * `bob measure metrics`: to compute
       thresholds and evaluate performances       * `bob measure roc`: to plot
       ROC       * `bob measure det`: to plot DET       * `bob measure hist`:
       to plot histograms       * `bob measure epc` : to plot EPC       * `bob
       measure evaluate`: applies all the above commands at once       * `bob
       measure gen`: to generate fake scores for `bob.measure`    Each command
       accepts one or several (dev,eval) score(s) file(s) for each system.
     - bob.measure!61 Title and histograms subplots: Account for this
       bob.bio.base!146#note_28760.
       *  Titles can be remove using an empty string, i.e. `-t ' '`  *
          Histograms support subplot display, see options `--subplots`  *  Add
          `--legends-ncol` option
     - bob.measure!62 Improve legends in histograms
     - bob.measure!48 recompute far values in roc_for_far: Fixes bob.measure#27
     - bob.measure!44 Compute roc using roc_for_far internally: Fixes
       bob.measure#26
     - bob.measure!43 Resolve "FAR and FRR thresholds are computed even when
       there is no data support": Closes bob.measure#27     Also changes
       behavior of far_threshold and frr_threshold where the returned threshold
       guarantees the at most the requested far/frr value.
     - bob.measure!63 Enable semilogx option in roc curves: * Fixes
       bob.measure#40   * Remove 0 points on x-axis in semilogx plots.
       Matplotlib 2 was doing this automatically before but matplotlib 2.2
       doesn't  * Code clean-up
     - bob.measure!64 Fix semilog plots for non numpy arrays: Fixes
       bob.bio.base#117
     - bob.measure!65 Modification of criterion_option: Correct display of
       available criteria
     - bob.measure!66 Add prefix aliasing: Prefix aliasing using AliasedGroup
       for bob.extension
     - bob.measure!68 Change --eval option default and Various fixes: Change
       defaults, clean unused options for histograms.    Fix bob.bio.base#112
     - bob.measure!69 Explain that the thresholds might not satisfy the
       requested criteria: *  Add a helper eer function for convenience.
     - bob.measure!50 Generic loading input file: Add a generic input file
       loading function for bob measure and its corresponding test.  From issue
       bob.measure#39, comments bob.measure#39#note_26366.
     - bob.measure!71 Fix issues with matplotlib.hist.: For some reason
       `mpl.hist` hangs when `n_bins` is set to `auto`.    This is related with
       https://github.com/numpy/numpy#8203    This MR set the default value to
       `doane`.  Furthermore, allows you to pick one of the options here
       https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html#numpy.histogram
       This will fix one of the points here bob.pad.base!43
     - bob.measure!72 Various improvements: Fix bob.measure#41 and
       bob.measure#42
     - bob.measure!70 Improvements to new metrics codes
     - bob.measure!73 Histogram legends: Fix bob.measure#44
     - bob.measure!74 Bins histograms: Option only depends on the number of
       data plotter per histograms, not the number of system. For example, pad
       hist requires 2 nbins and vuln hist requires 3 independently on the
       number of systems to be plotted.    Fix bob.measure#45.
     - bob.measure!75 Fix issue with histo legends: Fix bob.measure#47     Also
       change default for number of legend columns.  Add comments and doc in
       the code for Hist.
     - bob.measure!76 Histo fix: Fix typo and bob.pad.base!43#note_31884
     - bob.measure!77 dd lines for dev histograms: See
       bob.pad.base!43#note_31903
     - bob.measure!78 Metrics: All stuff related to bob.measure#46.
     - bob.measure!79 Add a command for multi protocol (N-fold cross
       validation) analysis
     - bob.measure!80 Consider non 1 values negatives: This will make
       bob.measure scripts work with FOFRA scores
     - bob.measure!81 Compute HTER using FMR and FNMR: As discussed in the
       meeting. Fixes bob.measure#48
     - bob.measure!83 Enable grid on all histograms
     - bob.measure!84 Improve the constrained layout option
     - bob.measure!82 Various fixes: * Change measure metrics   * Document and
       change HTER  * add decimal precision option for metric  * Use acronyms
       instead of full names in figures  * Remove filenames form figures and
       add log output instead
     - bob.measure!86 Fix decimal number control for metrics: Fixes
       bob.measure#52
     - bob.measure!88 Fix tests: Should fix bob.nightlies#40
     - bob.measure!67 Titles: Allow list of titles and remove `(development)`
       `(evaluation)` when default titles are modified
     - bob.measure!45 Condapackage
     - bob.measure!85 Fix broken commands cref bob.extension!86
     - bob.measure!53 Change the way the scores arguments are passed to the
       compute() function: it now: Change the way the scores arguments are
       passed to the compute() function: it now does not rely on dev,eval pairs
       anymore and can take any number of different files (e.g. train)
     - bob.measure!87 Update documentation and commands: FAR->FPR, FRR->FNR:
       Fix bob.measure#54
* bob.io.image
  * patch
     - bob.io.image!41 Resolve "versions of image libraries are evaluated by
       hand and given as parameters on the compiler command line": Closes
       bob.io.image#32
* bob.db.base
  * patch
     - bob.db.base!42 Handle errors when loading db interfaces: Fixes
       bob.db.base#24
* bob.io.video
  * v2.1.1 (Apr 17, 2018 11:06)
     - Sligthly increased noise test parameters on mp4 files with mpeg2video codecs (closed #11)
* bob.io.matlab
  * patch
* bob.io.audio
  * patch
     - bob.io.audio!7 Resolve "version relies on compiler command line
       parameter": Closes bob.io.audio#6
* bob.sp
  * patch
* bob.ap
  * patch
     - [sphinx] Fixed doc tests
* bob.ip.base
  * patch
     - bob.ip.base!16 Add a block_generator function. Fixes bob.ip.base#11
     - [sphinx] Fixed doc tests
* bob.ip.color
  * patch
* bob.ip.draw
  * patch
* bob.ip.gabor
  * patch
* bob.learn.activation
  * patch
* bob.learn.libsvm
  * patch
     - bob.learn.libsvm!9 Resolve "LIBSVM_VERSION is passed as a string to the
       compiler, but evaluated as uint64_t in the code": Closes
       bob.learn.libsvm#10
* bob.learn.linear
  * patch
     - [sphinx] Fixed doc tests
* bob.learn.mlp
  * patch
     - [sphinx] Fixed doc tests
* bob.learn.boosting
  * patch
* bob.db.iris
  * patch
* bob.learn.em
  * patch
     - [sphinx] Fixed doc tests
* bob.db.wine
  * patch
* bob.db.mnist
  * patch
* bob.db.atnt
  * patch
* bob.ip.facedetect
  * patch
     - [sphinx] Fixed doc tests
* bob.ip.optflow.hornschunck
  * patch
* bob.ip.optflow.liu
  * patch
* bob.ip.flandmark
  * patch
* gridtk
  * patch
     - gridtk!21 remove the submitted command line column when not long: Fixes
       gridtk#27
     - gridtk!20 Resolve "jman fails when jobs are deleted before they are
       finished": Closes gridtk#26
     - gridtk!22 Memory argument sets gpumem parameter for gpu queues: Fixes
       gridtk#24
     - gridtk!23 Accept a plus sign for specifying the job ranges
* bob.ip.qualitymeasure
  * patch
* bob.ip.skincolorfilter
  * patch
* bob.ip.facelandmarks
  * patch
* bob.ip.dlib
  * patch
     - bob.ip.dlib!13 Removed bob_to_dlib_image_convertion functions and
       replaced them to bob.io.image.to_matplotlib: CLoses bob.ip.dlib#6
     - bob.ip.dlib!11 Fix in the download mechanism
* bob.ip.mtcnn
  * v0.0.1 (May 23, 2018 17:56)
     * First release
     - bob.ip.mtcnn!4 Added conda recipe: Closes bob.ip.mtcnn#2     We don't
       have a caffe for Mac OSX in the defaults channel.   This can be an issue
       for the bob.pad.face builds.
     - bob.ip.mtcnn!5 Deleted the fuctions bob_to_dlib_image_convertion and…:
       Deleted the fuctions bob_to_dlib_image_convertion and
       dlib_to_bob_image_convertion and replaced them by the
       bob.io.color.to_matplotlib    Closes bob.ip.mtcnn#3     [sphinx] Fixed
       plots
     - bob.ip.mtcnn!6 [conda] Fixed conda recipe for the nightlies build issue
       bob.ip.mtcnn#5: Closes bob.ip.mtcnn#5
  * v1.0.0 (May 23, 2018 20:01)
     * First release
  * patch
* bob.db.arface
  * patch
* bob.db.asvspoof
  * patch
* bob.db.asvspoof2017
  * patch
     - bob.db.asvspoof2017!5 Update link to avspoof 2017
* bob.db.atvskeystroke
  * patch
* bob.db.avspoof
  * patch
* bob.db.banca
  * patch
* bob.db.biosecure
  * patch
* bob.db.biosecurid.face
  * patch
* bob.db.casme2
  * patch
* bob.db.caspeal
  * patch
* bob.db.cohface
  * patch
* bob.db.frgc
  * patch
* bob.db.gbu
  * patch
* bob.db.hci_tagging
  * patch
* bob.db.kboc16
  * patch
* bob.db.lfw
  * patch
* bob.db.livdet2013
  * patch
* bob.db.mobio
  * patch
* bob.db.msu_mfsd_mod
  * patch
* bob.db.multipie
  * patch
* bob.db.nist_sre12
  * patch
* bob.db.putvein
  * patch
* bob.db.replay
  * patch
* bob.db.replaymobile
  * patch
     - bob.db.replaymobile!10 Ignore all exceptions when closing the session
* bob.db.scface
  * patch
* bob.db.utfvp
  * patch
* bob.db.verafinger
  * patch
* bob.db.fv3d
  * patch
* bob.db.hkpu
  * patch
     - bob.db.hkpu!2 Antecipated issue with conda-build. Check bob.db.ijbc!1
* bob.db.thufvdt
  * patch
* bob.db.mmcbnu6k
  * patch
     - bob.db.mmcbnu6k!2 Antecipated issue with conda-build. Check
       bob.db.ijbc!1
* bob.db.hmtvein
  * patch
     - bob.db.hmtvein!2 Antecipated issue with conda-build. Check bob.db.ijbc!1
* bob.db.voicepa
  * patch
* bob.db.xm2vts
  * patch
* bob.db.youtube
  * patch
* bob.db.pericrosseye
  * patch
* bob.bio.base
  * major
     - Breaking and significant changes
     - Removed the old ``evaluate.py`` script.
     - Functionality to load biometric scores are now in ``bob.bio.base.score``
     - Added new scripts for plotting and evaluations. Refer to docs.
     - Added a new baselines concept. Refer to docs.
     - Detailed changes
     - bob.bio.base!147 Update installation instructions since conda's usage
       has changed.
     - bob.bio.base!148 Archive CSU: closes bob.bio.base#109
     - bob.bio.base!146 Add 4-5-col files related functionalities  and add
       click commands: In this merge:  *  Add loading functionalities from
       `bob.measure`  *  Add the following click commands (as substitutes for
       old script evaluate.py) using 4- or 5 - scores input files:      * `bob
       bio metrics`      * `bob bio roc`      * `bob bio det`      * `bob bio
       epc`      * `bob bio hist`      * `bob bio evaluate` : calls all the
       above commands at once      * `bob bio cmc`      * `bob bio dic`      *
       `bob bio gen`    Plots follow ISO standards.  The underlying
       implementation of the mentioned commands uses `bob.measure` base
       classes.    Fixes bob.bio.base#108
     - bob.bio.base!149 Set io-big flag for the demanding grid config: Closes
       bob.bio.base#110     Anyone cares to review this one?    It's harmless.
     - bob.bio.base!143 Set of click commands for bio base: From
       bob.bio.base#65    Provide commands in bio base:  - bob bio metrics
       - bob bio roc  - bob bio evaluate (Very similar to evalute.py)
     - bob.bio.base!152 Removed unused import imp and solving bob.bio.base#83:
       Closes bob.bio.base#83
     - bob.bio.base!153 Added the protocol argument issue bob.bio.base#111:
       Closes bob.bio.base#111
     - bob.bio.base!154 Fixes in ROC and DET labels
     - bob.bio.base!157 Fixed bob bio dir x_labels and y_labels: The labels of
       the DIR plot were incorrect.
     - bob.bio.base!155 Write parameters in a temporary config file to enable
       chain loading: Fixes bob.bio.base#116
     - bob.bio.base!150 Exposing the method groups in our FileDatabase API
     - bob.bio.base!158 Add prefix aliasing for Click commands
     - bob.bio.base!160 Titltes: Allows a list of titles    Fixes
       bob.bio.base#121.    Requires bob.measure!67
     - bob.bio.base!159 Resolve "Documentation does not include a link to the
       recordings of the IJCB tutorial": Closes bob.bio.base#122
     - bob.bio.base!161 Change --eval option default and Various fixes: fixes
       bob.bio.base#112.    Add and clean histo options. See
       bob.measure!67#note_30951 Requires bob.measure!68
     - bob.bio.base!163 Reduce repition between commands: Depends on
       bob.measure!70
     - bob.bio.base!162 Removed traces of evaluate.py in the documentation
     - bob.bio.base!164 Fix test according to changes in nbins option
     - bob.bio.base!165 Set names for different bio metrics: Bio specific names
       for metrics when using bob.measure Metrics
     - bob.bio.base!166 Add a command for multi protocol (N-fold cross
       validation) analysis: Similar to bob.measure!79
     - bob.bio.base!167 Various fixes: Requires bob.measure!82   Similar to
       bob.measure!82 for bio commands
     - bob.bio.base!168 Documentation changes in bob bio annotate: Depends on
       bob.extension!86
     - bob.bio.base!156 Using the proper verify script depending on system:
       Closes bob.bio.base#119
     - bob.bio.base!151 Created the Baselines Concept
     - bob.bio.base!169 Change assert to assert_click_runner_result
* bob.bio.gmm
  * patch
     - bob.bio.gmm!19 Fix bob.measure->bob.bio.base related issues: Fixes
       bob.bio.gmm#25
     - bob.bio.gmm!20 argument allow_missing_files wrongly passed to qsub
     - bob.bio.gmm!21 IVector - Fix LDA rank: With this MR we make sure that
       the dimension of the LDA matrix is not higher than its rank.
* bob.bio.face
  * major
     - Breaking changes:
     - Dropped support for CSU baselines
     - Detailed changes:
     - bob.bio.face!47 Accept an annotator in FaceCrop: related to
       bob.bio.face#26
     - bob.bio.face!48 Dropped support to CSU baselines issue bob.bio.face#29
     - bob.bio.face!51 Removing baselines: Related to this MR bob.bio.face!49
     - bob.bio.face!50 Ijbc highlevel
     - bob.bio.face!49 Refactoring baselines: Now we can all the facerec
       baselines can be reached via  ``bob bio baselines --help``. Refer to
       docs.
* bob.bio.spear
  * patch
     - bob.bio.spear!40 Handle mute audio correctly: Fixes bob.bio.spear#31
* bob.bio.video
  * patch
     - bob.bio.video!35 Add video wrappers using chain loading: Fixes
       bob.bio.video#12
     - bob.bio.video!36 Load videos frame by frame in annotators: Related to
       bob.bio.video#13
* bob.bio.vein
  * patch
     - bob.bio.vein!42 Fix bob.measure->bob.bio.base related issues
     - bob.bio.vein!43 Using the new bob.bio API
     - bob.bio.vein!44 Fixing comparison: Closes bob.bio.vein#18
* bob.db.voxforge
  * patch
     - bob.db.voxforge!20 Handling the --help command in download_and_untar
       script: Fixes bob.db.voxforge#12
     - bob.db.voxforge!18 Fixed the index.rst to match joint docs requirements
* bob.rppg.base
  * v1.1.0 (Jun 22, 2018 08:58)
     - Initial conda release for rPPG algorithms
     - Bug correction in the CHROM algorithm
     - Python 2 and 3 compatibility
     - Improved documentation (mostly Python API)
  * v2.0.0 (Jun 27, 2018 15:52)
     - getting rid of bob.db.* dependencies
     - usage of configuration files
  * patch
     - bob.rppg.base!8 Resolve "Potential bug when computing average color from
       mask": Closes bob.rppg.base#15
     - bob.rppg.base!7 Fixed recipe to test all modules
* bob.pad.base
  * minor
     - Significant changes:
     - Added new plotting and evaluation scripts. Refer to docs.
     - Detailed Changes:
     - bob.pad.base!52 Change assert to assert_click_runner_result
     - bob.pad.base!50 Add new classification algorithms: As mentioned here
       bob.pad.base!33 here is the new branch
     - bob.pad.base!51 Fix broken commands cref bob.extension!86
     - bob.pad.base!48 Various fix: Requires bob.measure!82    Similar to
       bob.measure!82 for PAD
     - bob.pad.base!45 Allow PAD filelist database to be used in vulnerability
       experiments
     - bob.pad.base!47 Remove bob vuln metrics and evaluate commands: since
       they were not well defined and we do  not know what should be in there.
       rename --hlines-at to --fnmr in bob vuln roc,det commands    small
       nit-pick fixes overall
     - bob.pad.base!43 Finalization of plots: Fixes bob.pad.base#22. Requires
       merge bob.measure!65. Requires bob.measure!67
     - bob.pad.base!46 Add a command for multi protocol (N-fold cross
       validation) analysis: Depends on bob.measure!79
     - bob.pad.base!44 Remove the grid_search.py entrypoint: Fixes
       bob.pad.base#23
     - bob.pad.base!41 Set of click commands for pad: Provide commands:    bob
       pad metrics  bob pad epc  bob pad epsc  bob pad gen
     - bob.pad.base!42 Set of click commands for pad: Provide commands:    bob
       pad metrics  bob pad epc  bob pad epsc  bob pad gen
     - added MLP and LDA classifiers for PAD
* bob.pad.face
  * minor
     - bob.pad.face!68 Improve load_utils.py: *  Plus some minor fixes to the
       frame-diff method
     - bob.pad.face!67 HLDI for the CelebA database and quality estimation
       script: This MR contains two contributions:  1.  The High Level DB
       interface for the CelebA database.  2.  The quality assessment script +
       config file allowing to estimate the quality of preprocessed CelebA
       images.
     - bob.pad.face!66 Added an option to exclude specific types of attacks
       from train set in BATL DB: This allows to exclude specific PAIs from the
       training set of the BATL DB. PAIs currently handled: makeup.
     - bob.pad.face!65 Updated the HLDI of BATL DB, added FunnyEyes fix, and
       protocol joining test and dev sets
     - bob.pad.face!64 Add support for external annotations in replaymobile
     - bob.pad.face!60 Change the API of yield_faces
     - bob.pad.face!62 Add a script for analyzing database face sizes
     - added preprocessors and extractors for pulse-based PAD.
* bob.pad.voice
  * v1.0.5 (Jun 27, 2018 16:00)
     - Fix imports and add an alias for PadVoiceFile
     - experimental audio eval: support for 2, 3 layers lstms
     - Fix error related to bob.measure->bob.bio.base movings Fixes
       bob.pad.voicebob.pad.voice#4
     - bob.pad.voice!14 Fix error related to bob.measure->bob.bio.base movings:
       Fixes bob.pad.voice#4
     - bob.pad.voice!15 Fix imports and add an alias for PadVoiceFile
  * patch
     - Fix avspoof db interface (added annotations method) !16
* bob.pad.vein
  * patch
     - Fix database tests
* bob.fusion.base
  * patch
     - bob.fusion.base!7 Major refactoring: Fixes bob.fusion.base#3   Fixes
       biometric/software#7  Fixes biometric/software#8
     - bob.fusion.base!8 improve behaviour and tests
     - bob.fusion.base!9 Fix the boundary script due to changes in
       bob.extension: Fixes bob.fusion.base#7
* bob.db.oulunpu
  * patch
     - bob.db.oulunpu!3 Training depends on protocol
     - bob.db.oulunpu!4 Add protocol 1_2
* bob.db.uvad
  * patch
     - bob.db.uvad!2 Convert annotations to properties
* bob.db.swan
  * patch
     - bob.db.swan!2 DRY
     - bob.db.swan!3 Recreate the PAD protocols and add a global face and voice
       pad protocol
* bob.db.cuhk_cufs
  * v2.2.1 (May 23, 2018 16:55)
     * Removed deprecated entrypoints
     - bob.db.cuhk_cufs!8 Removing deprecated entry-points: Removing deprecated
       entry-points    fixing bob.db.cuhk_cufs!7
  * patch
* bob.db.cbsr_nir_vis_2
  * v2.0.2 (May 23, 2018 17:35)
     * Removed deprecated entrypoints
     * Ported to the new CI
  * patch
* bob.db.nivl
  * v0.0.1 (May 23, 2018 18:15)
     * First release
  * v1.0.0 (May 24, 2018 11:37)
     * First release
  * patch
* bob.db.pola_thermal
  * v0.0.1 (May 23, 2018 18:57)
     * First release
  * v1.0.0 (May 24, 2018 11:54)
     * First release
  * patch
* bob.db.cuhk_cufsf
  * v0.0.1 (May 23, 2018 19:10)
     * First release
  * v1.0.0 (May 24, 2018 12:09)
     * First release
  * patch
* bob.db.ijba
  * patch
     - bob.db.ijba!13 Fix bob.measure->bob.bio.base related issues
* bob.ip.tensorflow_extractor
  * v0.0.2 (Apr 27, 2018 15:16)
     - added DR-GAN extractor
  * patch
     - Replaced the download_model method to the new one implemented in
       bob.extension !7
     - Fixed conda-build issue !8
* bob.ip.caffe_extractor
  * v2.0.0 (Jun 30, 2018 12:22)
     * Added Light CNN bob.ip.caffe_extractor!6 bob.ip.caffe_extractor!7
     * Created conda package of it bob.ip.caffe_extractor!9
     * Replaced the download_model method to the new one implemented in
       bob.extension bob.ip.caffe_extractor!10
     - bob.ip.caffe_extractor!10 Replaced the download_model method to the new
       one implemented in bob.extension: Closes bob.ip.caffe_extractor#6     I
       already updated the URL in this one
  * patch
* bob.bio.caffe_face
  * patch
* bob.db.maskattack
  * patch
     - first release
