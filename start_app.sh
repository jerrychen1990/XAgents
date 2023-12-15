#!/bin/bash
echo 'stopping old app'
ps aux | grep streamlit | grep app | grep 8603 |awk '{print $2}' | xargs -t kill
sleep 1

# export PYTHONPATH=`pwd`

conda activate xagent

echo 'starting app service'
$CONDA_PREFIX/bin/streamlit run app.py --server.port 8603  true 2>&1 | tee ${LOG_HOME}/xagent_app.log
echo 'start app done'


