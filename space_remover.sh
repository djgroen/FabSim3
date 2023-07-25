function fabsim_autocomplete() {
    local cmd="$*"
    local modified_cmd=""
    local arr=""

    # Modify the command to preserve only the first two spacesa

    segment=$(echo "$cmd" | cut -d ' ' -f 2-100)
    machine=$(echo "$cmd" | cut -d ' ' -f 1)

    modified_cmd=$(echo "$segment" | sed 's/\(  *\)//g')

    # Execute the modified command
    eval "fabsim $machine $modified_cmd"
}


