


targetDir=$HOME/bin
target=$targetDir/ceda_cc

#### 1. Make target directory is not present
###############################################

if [ ! -d "$targetDir" ]; then
  # Control will enter here if $targetDir doesn't exist.
  echo creating directory $targetDir
  mkdir $targetDir
fi

#### 2. Create a script
###############################################

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

#### 2. Make the script executable
###############################################
chmod u+x $target 
