import pathlib
from multiprocessing.managers import BaseProxy
from typing import Iterator
import os
import csv


def abspath(name: str) -> pathlib.Path:
    return pathlib.Path(name).absolute()


def create_filename(hostname: str, filename: str) -> str:
    """
    Outputs filenames with any illegal characters removed.
    """
    result = f"{hostname}_{filename}.txt"
    illegals = list(" <>:\\/|?*\0$")
    illegals.extend(["CON", "PRN", "AUX", "NUL", "COM", "LPT"])
    for illegal_string in illegals:
        result = result.replace(illegal_string, "_")
    return result


def set_dir(name: str, log_q: BaseProxy):
    """
    Helper function to create (and handle existing) folders and change directory to them automatically.
    """
    try:
        abspath(name).mkdir(parents=True, exist_ok=True)
        log_q.put(f"debug set_dir: abspath({name}).mkdir()")
    except Exception as e:
        log_q.put(
            f"warning Could not create {name} directory in {os.getcwd()}\nReason {e}"
        )
    try:
        os.chdir(name)
        log_q.put(f"debug set_dir: os.chdir({name})")
    except Exception as e:
        log_q.put(
            f"warning Could not change to {name} directory from {os.getcwd()}\nReason {e}"
        )


def load_jobfile(filename: pathlib.Path) -> Iterator[str]:
    with open(
        filename,
        "r",
        newline="",
    ) as joblist:
        for job_entry in joblist:
            yield job_entry.strip()


def read_config(filename: pathlib.Path, log_q: BaseProxy) -> Iterator[dict]:
    """
    Generator function to processes the CSV config file. Handles the various CSV formats and removes headers.
    """
    with open(filename, "r") as config_file:
        log_q.put(f"debug read_config: filename: {filename}")
        dialect = csv.Sniffer().sniff(config_file.read(1024))  # Detect CSV style
        config_file.seek(0)  # Reset read head to beginning of file
        reader = csv.reader(config_file, dialect)
        header = next(reader)
        log_q.put(f"debug read_config: header: {header}")
        for config_entry in reader:
            yield dict(zip(header, config_entry))


def preload_jobfile(
    jobfile: pathlib.Path,
    log_q: BaseProxy,
) -> BaseProxy:
    """
    Load the job file beforehand and put them in a Proxied list. This lets each process grab the list from memory than spending disk IOPS on it
    """
    result = list(load_jobfile(jobfile))
    log_q.put(f"debug Added {jobfile} to cache")
    return result
