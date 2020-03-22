while :
do
  # regular expression looks for python followed by source.py
  if test $(ps aux | grep -E ^.*python.*source.py$); then 
    echo "$(date): process exists."
    sleep 600 # 60 seconds * 10 minutes
  else
    echo "$(date): process restarting."

    # ADD PYTHON COMMAND HERE
    python ./arxivedits/source.py 2>&1 | tee -a ./arxivedits/log.txt &
    
    echo "$(date): process restarted." 
    sleep 10 # sleep 2 seconds, wait for the process to restart
  fi
done
