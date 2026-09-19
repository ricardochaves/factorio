#!/bin/zsh
cd "${0:A:h}"
python3 gen.py > gen_full.log 2>&1 && tail -1 gen_full.log
python3 build_book.py 2>&1 | tail -1
python3 deep_verify.py ../blueprints/belt-balancers/blue-belt.txt 2>&1 | head -6
python3 export_tests.py ../blueprints/belt-balancers/blue-belt.txt | tail -1
./run_ingame.sh 3400 > ingame_run_final.log 2>&1
python3 analyze_ingame.py > ingame_analysis_final.txt 2>&1; head -11 ingame_analysis_final.txt | cut -c1-200; tail -1 ingame_analysis_final.txt | cut -c1-200
rm -rf ingame/data/saves
(cd xcheck && python3 xcheck.py ../../blueprints/belt-balancers/blue-belt.txt > final_book.log 2>&1; tail -1 final_book.log; grep -cE "\[.*D" final_book.log)
echo PIPELINE_DONE
