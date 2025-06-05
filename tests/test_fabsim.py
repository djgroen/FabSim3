import os
import sys
import subprocess
import pytest
import fileinput
import re


@pytest.mark.parametrize(
    "execute_cmd,search_for,cnt",
    [
        (
            "fabsim localhost install_plugin:FabDummy",
            "FabDummy plugin installed",
            1,
        ),
        (
            "fabsim localhost dummy:dummy_test,manual_ssh=false",
            "dummy test has been concluded",
            1,
        ),
        (
            "fabsim localhost dummy:dummy_test,manual_ssh=true",
            "dummy test has been concluded",
            1,
        ),
        (
            "fabsim localhost dummy:dummy_test,replicas=5,nb_process=2,manual_ssh=false",
            "dummy test has been concluded",
            5,
        ),
        (
            "fabsim localhost dummy_ensemble:dummy_test,nb_process=2,manual_ssh=false",
            "dummy test has been concluded",
            3,
        ),
        (
            "fabsim localhost dummy_ensemble:dummy_test,nb_process=2,manual_ssh=true",
            "dummy test has been concluded",
            3,
        ),
        (
            "fabsim localhost dummy_ensemble:dummy_test,replicas=5,nb_process=2,manual_ssh=false",
            "dummy test has been concluded",
            15,
        ),
        (
            "fabsim localhost dummy_ensemble:dummy_test,replicas=5,nb_process=2,manual_ssh=true",
            "dummy test has been concluded",
            15,
        ),
    ],
    indirect=["execute_cmd"],
    ids=[
        "FabDummy installation",
        "FabDummy without manual SSH",
        "FabDummy with manual SSH",
        "FabDummy replicas without manual SSH",
        "FabDummy ensemble without manual SSH",
        "FabDummy ensemble with manual SSH",
        "FabDummy ensemble replicas without manual SSH",
        "FabDummy ensemble replicas with manual SSH",
    ],
)
def test_fabsim(execute_cmd, search_for, cnt):
    cmd_output = execute_cmd
    assert len(re.findall(search_for, cmd_output)) == cnt
