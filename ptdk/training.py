import os
import subprocess
import tempfile
import re
import shutil
import uuid
from pathlib import Path

import bioblend

from flask import Blueprint, flash, render_template, request

from planemo import cli
import planemo.commands.cmd_workflow_test_init as WorkflowTestInit

PTDK_DIRECTORY = os.getcwd()


class PtdkException(Exception):
    pass


tuto = Blueprint("training", __name__)

config = {
    "usegalaxy.eu": {
        "url": "https://usegalaxy.eu/",
    },
    "usegalaxy.org.au": {
        "url": "https://usegalaxy.org.au/",
    },
    "usegalaxy.org": {
        "url": "https://usegalaxy.org/",
    },
    "usegalaxy.fr": {
        "url": "https://usegalaxy.fr/",
    },
}


def check_metadata(tuto):
    """Check the metadata for a tutorial"""
    error = None
    if not tuto["galaxy_url"]:
        error = "Galaxy URL is required."
    elif not tuto["invocation_id"]:
        error = "Workflow id is required."
    elif not tuto["api_key"]:
        error = "API Key is required."
    elif tuto["galaxy_url"] not in config:
        error = "Unsupported Galaxy instance."
    return error


def generate(tuto):
    """Generate skeleton of a tutorial"""
    try:
        out = subprocess.check_output([
            'planemo',
            'workflow_test_init',
            '--from_invocation', tuto['invocation_id'],
            '--galaxy_url', tuto['galaxy_url'],
            '--galaxy_user_key', tuto['api_key'],
        ])
        print(out)
    except:
        pass


@tuto.route("/", methods=("GET", "POST"))
def index():
    """Get tutorial attributes"""
    if request.method == "POST":
        print("POST", request.form)

        tuto_metadata = {
            "uuid": str(uuid.uuid4())[:8],
            "galaxy_url": request.form["galaxy_url"],
            "invocation_id": request.form["workflow_id"],
            "api_key": request.form["api_key"],
        }
        print(tuto_metadata)
        error = check_metadata(tuto_metadata)
        tuto_metadata['galaxy_url'] = config[tuto_metadata['galaxy_url']]['url']

        if error is not None:
            flash(error)
            return render_template("training/index.html", servers=config.keys())

        with tempfile.TemporaryDirectory() as twd:
            output_path = None
            try:
                # Move into the temp directory for maximum safety
                os.chdir(twd)

                # All of the subsequent file generation is done in there.
                # We get back a filename (relative to twd)
                generate(tuto_metadata)


                zip_fn = f"ptdk-{tuto_metadata['invocation_id']}-{tuto_metadata['uuid']}"
                print(f"zip_fn: {zip_fn}")
                # Here's where we want the final output to go.
                output_name = Path("static") / Path(zip_fn + '.zip')
                print(f"output_name: {output_name}")
                output_path = Path(PTDK_DIRECTORY) / Path("ptdk") / Path("static") / Path(zip_fn)
                print(f"output_path: {output_path}")
                shutil.make_archive(output_path, "zip", twd)
            except Exception as err:
                print(f"ERROR: {tuto_metadata['uuid']}: {err}")
                flash(f"An error occurred: {tuto_metadata['uuid']}.")
                return render_template("training/index.html", servers=config.keys())
            finally:
                os.chdir(PTDK_DIRECTORY)

            return render_template("training/index.html", zip_fp=output_name, servers=config.keys())

    return render_template("training/index.html", servers=config.keys())
