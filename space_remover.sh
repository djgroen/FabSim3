function fabsim_modified_execution() {
    local cmd="$*"
    local modified_cmd=""
    local arr=""

    # Check if the command starts with "fabsim"
    if [[ "$cmd" == "fabsim"* ]]; then
        # Modify the command to preserve only the first two spacesa

        segment=$(echo "$cmd" | cut -d ' ' -f 3-100)
        machine=$(echo "$cmd" | cut -d ' ' -f 2)

        modified_cmd=$(echo "$segment" | sed 's/\(  *\)//g')

        # Execute the modified command
        eval "fabsim $machine $modified_cmd"
    else
        # Execute the original command as it is
        eval "$cmd"
    fi
}

