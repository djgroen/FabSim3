#!/bin/bash

# Display a message when the script is sourced
echo "FabSim Custom Autocomplete!"

# Instructions for using autocompletion
echo "To use autocompletion:"
echo " - Start typing a <COMMAND><SPACE><TAB> to see suggestions."
echo " - For machines, type 'fabsim<SPACE><TAB>' to see available machines."
echo " - For stanalone tasks, type 'fabsim localhost<SPACE><TAB>' to see available options."
echo " - For options with argument(s), type 'fabsim localhost flare_local:<TAB>' to see available options."
echo " - If autocomplete does not provide options, please 'source autocomplete.sh' script again."

_fabsim_completion() {

    local cur prev1 prev2
    # Get the current word being completed and the previous two words
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev1="${COMP_WORDS[COMP_CWORD-1]}"
    prev2="${COMP_WORDS[COMP_CWORD-2]}"

    # Check if the FABSIM3_HOME environment variable is set
    if [[ -z "${FABSIM3_HOME}" ]]; then
        echo "Error: FABSIM3_HOME environment variable is not set!"
        return 1
    fi

    # Check if the autocomplete.py file exists in the FABSIM3_HOME directory
    if [[ ! -f "${FABSIM3_HOME}/autocomplete.py" ]]; then
        echo "Error: autocomplete.py file not found!"
        return 1
    fi

    # Run the generate_tasks_dict.py script and capture its output
    python_output=$(python "${FABSIM3_HOME}/autocomplete.py")

    # Function to parse the Python output and populate the bash associative arrays
    parse_python_output() {
        local python_output=$1

        # Clear any previous data in machines_dict and tasks_dict
        machines_dict=()
        tasks_dict=()

        # Parse the JSON using jq and convert it to an associative array in bash
        while IFS="=" read -r key value; do
            if [[ "$key" == "machines" ]]; then
                machines_dict["$key"]=$value
            else
                tasks_dict["$key"]=$value
            fi
        done < <(echo "$python_output" | jq -r 'to_entries | map("\(.key)=\(.value)") | .[]')
    }

    # Declare associative arrays
    declare -A machines_dict
    declare -A tasks_dict

    # Call the function to populate the associative array
    parse_python_output "$python_output"

    # Function to modify the keys in the dictionary directly
    modify_keys() {
        local -n dict_name_ref="$1"  # Name of the dictionary variable as a reference

        # Create a new associative array to store the modified keys and values
        declare -A modified_dict

        # Modify keys here
        for key in "${!dict_name_ref[@]}"; do
            local value="${dict_name_ref[$key]}"
            if [[ "$value" == '[""]' ]]; then
                # For empty values, keep the key as it is
                modified_dict["$key"]="$value"
            else
                # For non-empty values, modify the key with e.g., ":<>"
                modified_dict["$key:"]="$value"
            fi
        done

        # Clear the original dictionary
        dict_name_ref=()

        # Copy the modified keys and values back to the original dictionary
        for key in "${!modified_dict[@]}"; do
            dict_name_ref["$key"]="${modified_dict[$key]}"
        done
    }

    # Function to process a single input string and extract the value
    modify_values() {
        local input_string="$1"

        # Create a variable to store the modified string
        local modified_string=""

        # Remove the outer square brackets and quotes from the input string
        modified_string="${input_string#[}"
        modified_string="${modified_string%]}"
        modified_string="${modified_string%\"}"
        modified_string="${modified_string#\"}"

        # Initialise the output string
        local output_string=""

        # Get the total number of words in the modified_string
        local total_words
        total_words=$(wc -w <<< "$modified_string")

        # Loop through the words in the modified_string and modify them individually
        for word in $modified_string; do
            # Modify the word (you can apply your custom logic here)
            modified_word="${word}=<>"

            # Append the modified word to the output_string
            output_string+="$modified_word"

            # Check if the current word is not the last word
            if [[ "$total_words" -gt 1 ]]; then
                # Append a comma after each word except the last word
                output_string+=","
            fi

            # Decrement the total_words count
            ((total_words--))
        done

        # Return the processed value
        echo "$output_string"
    }

    # Define a list of default options that users will always see
    default_options=("install_plugin:")

    # If the current word is the first argument, provide machines as completion options
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        local machines_values
        machines_values="${machines_dict["machines"]}"
        IFS=', ' read -r -a parsed_machines_values <<< "$machines_values"
        mapfile -t COMPREPLY < <(compgen -W "${parsed_machines_values[*]}" -- "${cur}")
        return 0
    fi

    # Your existing code for autocompletion based on the dictionaries
    if [[ ${COMP_CWORD} -eq 2 ]]; then
        if [[ -z "${tasks_dict[*]}" ]]; then
            # Tasks_dict is empty, provide default_options as completion options
            IFS=$'\n' read -r -d '' -a completions < <(compgen -W "${default_options[*]}" -- "${cur}"; printf '\0')

            # Set the completions with the modified keys
            COMPREPLY=("${completions[@]}")

            return 0
        else
            declare -A tasks_dict_copy=()
            for key in "${!tasks_dict[@]}"; do
                tasks_dict_copy["$key"]="${tasks_dict[$key]}"
            done

            # Modify keys in the copied associative array
            modify_keys "tasks_dict_copy"

            # Get the original keys (without modifications) for completions
            IFS=$'\n' read -r -d '' -a completions < <(compgen -W "${!tasks_dict_copy[*]}" -- "${cur}"; printf '\0')

            # Set the completions with the modified keys
            COMPREPLY=("${completions[@]}")

            return 0
        fi
    fi

    if [[ ! -z "${tasks_dict[*]}" ]]; then

        # Check if the user selects a key that matches the current word (prev1)
        for key in "${!tasks_dict[@]}"; do
            if [[ "$key" == "${prev1}" ]]; then
                local values="${tasks_dict[$key]}"

                # Call list processing function
                processed_values=$(modify_values "$values")

                # Add the processed values to COMPREPLY without a space after prev1
                COMPREPLY+=("${processed_values}")
                return 0
            fi
        done

        # Handle the scenario when the current word ends with a colon (':') and TAB is pressed
        if [[ $cur == *: && $prev2 != "" ]]; then
            local values="${tasks_dict[$prev2]}"

            # Call list processing function
            processed_values=$(modify_values "$values")

            # Append the values to COMPREPLY without a space after prev2
            COMPREPLY+=("${prev2}${processed_values}")
            return 0
        fi
    fi

    # If no completions are provided so far, fallback to default completion
    mapfile -t COMPREPLY < <(compgen -W "${tasks_dict[*]}" -- "$cur")
}

# Register the completion function
complete -o nospace -F _fabsim_completion fabsim
