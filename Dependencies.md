## Dependencies for FabSim3

pyyaml (3.12 tested)
fabric3 (1.13.1 tested)

## Note on using both Python2 fabric and fabric3 (e.g., when having both FabSim and FabSim3 installed)

Both versions of fabric map to the same command, which can lead to conflicts. I resolve this myself as follows.

* My Python2 fabric installation is in system-space, and that command maps to /usr/bin/fab.
* I install fabric3 using pip3 install fabric3 (no sudo). This creates a fab command in $HOME/.local/bin.
* I then create a symbolic link as follows "ln -s ~/local/bin/fab ~/bin/f3".
* Lastly, I add ~/bin to my $PATH environment variable in my Bash shell by putting "export PATH=$HOME/bin:${PATH}" in my .bashrc.

Now I can run 'fab' to execute FabSim related commands, and 'f3' to execute FabSim3 related commands. :)
