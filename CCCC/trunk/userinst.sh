


target=$HOME/bin/ceda_cc

echo Creating bash script in $target
cat > $target << EOF
#!/bin/bash
# CEDA CC entry script
# To execute python scripts in $PWD/ceda_cc
# License file: $PWD/LICENSE 
# Vocabularies: $PWD/ceda_cc/config

if [ \$1 == '-h' ];
  then
  cat $PWD/README.txt
  exit
fi

python $PWD/ceda_cc/c4.py \$*
EOF

chmod u+x $target 
