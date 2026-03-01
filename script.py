"""Script to extract information about the verbiage of given text files."""

import logging
import re
import socket
import subprocess
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import TextIOWrapper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

IF_TXT = Path(__file__).parent / "data" / "IF.txt"
ALWAYS_REMEMBER_US_TXT = Path(__file__).parent / "data" / "AlwaysRememberUsThisWay.txt"


def word_count(file: TextIOWrapper) -> int:
    """Count the number of words within a given file object.

    Args:
        file (TextIOWrapper): File object to count number of words in.

    Returns:
        int: Count of words in file
    """
    file.seek(0)  # reset location in file
    word_count = 0
    for line in file:
        word_count += len(line.split())
    logger.info(f"'{word_count}' words found in '{Path(file.name).name}'.")  # noqa: G004
    return word_count


def convert_contractions(line: str) -> str:
    """Convert basic contractions to their expanded version.

    Makes assumption that all *'s are contractions and not possessive.

    Args:
        line (str): String to expand contractions on.

    Returns:
        str: Expanded contractions version of the provided input.
    """
    # handle edge cases where additional work as to be done to convert contraction
    line = re.sub(r"won\'t", "will not", line)
    line = re.sub(r"can\'t", "can not", line)

    # handle base cases of converting contractions
    line = re.sub(r"n\'t", " not", line)
    line = re.sub(r"\'t", " not", line)
    line = re.sub(r"\'m", " am", line)
    line = re.sub(r"\'s", " is", line)
    line = re.sub(r"\'d", " would", line)
    line = re.sub(r"\'ve", " have", line)
    line = re.sub(r"\'ll", " will", line)
    return line  # noqa: RET504


def find_three_most_frequent_words(file: TextIOWrapper, *, handle_contractions: bool = False) -> list[tuple[str, int]]:
    """Count the frequency of words in the file obj, returning a list of the top 3 most frequency and their frequency.

    Args:
        file (TextIOWrapper): File object to calculate frequency of
        handle_contractions (bool, optional): Whether to expand contractions before computing the frequency or not.
            Defaults to False.

    Returns:
        list[tuple[str, int]]: Top 3 most occurring words return in tuple pairs (word, count)
    """
    file.seek(0)  # reset location in file
    individual_word_counts = Counter()
    for line in file:
        text_line = convert_contractions(line) if handle_contractions else line
        cleaned_words = re.sub(r"[^\w\s]", "", text_line).lower().split()
        individual_word_counts.update(cleaned_words)
    top3: list[tuple[str, int]] = individual_word_counts.most_common(3)
    logger.info(f"Most common words in '{Path(file.name).name}': {top3}")  # noqa: G004
    return top3


def get_ip_address() -> str:
    """Run a terminal command to find the IP Address of the Machine running the container.

    Tries to get the value of host.docker.internal first. If that is not found then it
    falls back to grabbing the default gateway IP.

    Returns:
        str: IP Address
    """
    try:
        host_ip = socket.gethostbyname("host.docker.internal")
        logger.info(f"Machine's IP Address: {host_ip}")  # noqa: G004
        return host_ip  # noqa: TRY300
    except socket.gaierror:
        pass

    # fallback to extracting the gateway ip address if host.docker.internal is not found
    try:
        result = subprocess.run(["ip", "route"], check=True)  # noqa: S607
        for line in result.stdout.splitlines():
            if not str(line).startswith("default"):
                continue
            gateway_ip = str(line).split()[2]
            logger.info(f"Machine's IP Address: {gateway_ip}")  # noqa: G004
            return gateway_ip
    except:  # noqa: E722
        logger.exception("IP Detection Failed")

    return ""


def results_to_text_file(  # noqa: PLR0913
    file1_name: str,
    file2_name: str,
    file1_word_count: int,
    file2_word_count: int,
    total_word_count: int,
    file1_top3: list[tuple[str, int]],
    file2_top3: list[tuple[str, int]],
    ip_address: str,
    *,
    output_path: Path = Path("result.txt"),
) -> None:
    """Write all of the collected data to the given output path.

    Args:
        file1_name (str): Name of first file
        file2_name (str): Name of second file
        file1_word_count (int): Word count of first file
        file2_word_count (int): Word count of second file
        total_word_count (int): Total word count of both files
        file1_top3 (list[tuple[str, int]]): Top 3 most occurring words in first file
        file2_top3 (list[tuple[str, int]]): Top 3 most occurring words in second file
        ip_address (str): IP address of Machine
        output_path (Path, optional): Path to write text to. Defaults to Path("result.txt").
    """
    # ensure directory exists before writing
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["File Parsing Results:", ""]

    # write file one results
    lines.append(f"File: {file1_name}")
    lines.append(f"\tWord Count: {file1_word_count}")
    top3_str = ", ".join([f"{word} ({count})" for word, count in file1_top3])
    lines.append(f"\tTop 3 Words: {top3_str}")
    lines.append("")

    # write file two results
    lines.append(f"File: {file2_name}")
    lines.append(f"\tWord Count: {file2_word_count}")
    top3_str = ", ".join([f"{word} ({count})" for word, count in file2_top3])
    lines.append(f"\tTop 3 Words: {top3_str}")
    lines.append("")

    # write non-file specific results
    lines.append(f"Total Word Count: {total_word_count}")
    lines.append(f"Machine IP Address: {ip_address}")
    lines.append("")

    output_path.write_text("\n".join(lines))
    logger.info(f"Wrote results to '{output_path}'")  # noqa: G004


def main() -> None:
    """Open the target files and compute information about the number and frequency of words in them."""
    # open IF.txt and AlwaysRememberUsThisWay.txt in /home/data
    with IF_TXT.open() as if_txt, ALWAYS_REMEMBER_US_TXT.open() as a_txt:
        # count the number of words in each file and calculate the total words between both
        if_txt_word_count = word_count(if_txt)
        a_txt_word_count = word_count(a_txt)
        total_word_count = if_txt_word_count + a_txt_word_count
        logger.info(
            f"'{total_word_count}' combined words found in '{Path(if_txt.name).name}' and '{Path(a_txt.name).name}'.",  # noqa: G004
        )

        # identify top 3 most frequent words in each file
        if_txt_top3 = find_three_most_frequent_words(if_txt)
        a_txt_top3 = find_three_most_frequent_words(a_txt, handle_contractions=True)

        # determine the ip address of the machine running the container
        ip = get_ip_address()

        # write results to home/data/output/result.txt
        results_to_text_file(
            file1_name=Path(if_txt.name).name,
            file2_name=Path(a_txt.name).name,
            file1_word_count=if_txt_word_count,
            file2_word_count=a_txt_word_count,
            total_word_count=total_word_count,
            file1_top3=if_txt_top3,
            file2_top3=a_txt_top3,
            ip_address=ip,
            output_path=Path(__file__).parent / "data" / "output" / "result.txt",
        )


if __name__ == "__main__":
    main()
