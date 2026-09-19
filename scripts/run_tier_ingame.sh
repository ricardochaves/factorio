#!/bin/zsh
# usage: run_tier_ingame.sh <tier>
cd "${0:A:h}"
export FBTIER=$1
python3 export_tests.py ../blueprints/belt-balancers/$1-belt.txt | tail -1
cat ingame/data/scenarios/balancer-test/tier.lua
./run_ingame.sh 12000 > ingame_run_$1.log 2>&1
python3 analyze_ingame.py > ingame_analysis_$1.txt 2>&1
rm -rf ingame/data/saves
grep elapsed ingame_run_$1.log; head -12 ingame_analysis_$1.txt | cut -c1-200; grep PROBLEMS ingame_analysis_$1.txt
echo TIER_DONE
