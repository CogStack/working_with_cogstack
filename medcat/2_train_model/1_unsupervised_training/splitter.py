
import re

import pydantic


class SplitIdentifier:
    start_line_start_pattern: re.Pattern = re.compile('(\d+),(\d+),')

    def is_first_line(self, line: str) -> bool:
        """Check if the line in question is a suitable first line for an entry.

        The schema:
        "subject_id","hadm_id","chartdate","charttime","text","category","description"

        However, "text" is often multiline.
        So an example first line could be:
        24776,139951,"2154-11-15 00:00:00","2154-11-15 17:48:00","HPI:
        That is, "subject_id","hadm_id","chartdate","charttime" and the start of "text"

        So currently, I am checking that the line:
        a) Starts with 2 integers separated by a comma
        b) Has an uneven number of quotation marks (i.e ends with an open quote)
        c) The number of quotes is greater than 4

        Args:
            line (str): The line in question

        Returns:
            bool: True if it's a suitable first line
        """
        # check if starts with 2 integers separated by comma
        if not self.start_line_start_pattern.match(line):
            return False
        nr_of_quotes = line.count('"')
        return (nr_of_quotes // 2) != (nr_of_quotes / 2) and nr_of_quotes > 4

    def is_last_line(self, line: str) -> bool:
        """Check if the lin in question is a suitable last line for an entry.

        The schema:
        "subject_id","hadm_id","chartdate","charttime","text","category","description"

        However, "text" is often multiline.
        So an example last line could be:
        ","Physician ","Physician Resident Progress Note"
        That is, the end of "text" and then "category","description"

        So currently I am checking that the line:
        a) Has an uneven number of quotation marks (i.e starts with an open quote)
        b) Number of quotes is greater than 4

        Args:
            line (str): The line in question

        Returns:
            bool: True if it's a suitable last line
        """
        nr_of_quotes = line.count('"')
        return (nr_of_quotes // 2) != (nr_of_quotes / 2) and nr_of_quotes > 4


class SplitOptions(pydantic.BaseModel):
    lines_at_a_time: int
    out_file_format: str
    header_length: int = 1


class SplitBuffer:

    def __init__(self, file_nr: int, opts: SplitOptions, split_identifier: SplitIdentifier, header: str) -> None:
        self.file_nr = file_nr
        self.opts = opts
        self.split_identifier = split_identifier
        self.lines: list = [header]
        self.prev_line_is_last = False
        self._is_done = False

    def save(self) -> None:
        file_name = self.opts.out_file_format % self.file_nr
        print('Saving', len(self.lines), 'to file nr',
              self.file_nr, ':', file_name)
        with open(file_name, 'w') as fw:
            fw.writelines(self.lines)

    def process_or_write(self, line_nr: int, line: str) -> 'SplitBuffer':
        """Process line and write if needed.

        If processing a line results in saving the data into a file, a new SplitBuffer is returned.
        This new instance will have the first line added to it already.
        If processing did not result in saving the data, the same instance is returned.

        Args:
            line_nr (int): The number of the line in the original
            line (str): The line contents

        Returns:
            SplitBuffer: Returns an instance of the buffer that should be used
        """
        if self._is_done:
            raise ValueError('Cannot reuse a SplitBuffer - create a new one')
        # line = line.replace('\n', '')
        has_passed_req_line = line_nr >= self.opts.lines_at_a_time * self.file_nr
        cur_line_is_last = self.split_identifier.is_last_line(line)
        cur_line_is_first = self.split_identifier.is_first_line(line)
        if has_passed_req_line and self.prev_line_is_last and cur_line_is_first:
            print('Currently at line', line_nr)
            self.save()
            # print('Saving', len(self.lines), 'up until', line_nr, 'to file number', self.file_nr, ':', out_file)
            # print('PREV line:\n', self.lines[-1])
            # print('NEW line:\n', line)
            self._is_done = True
            buffer = SplitBuffer(
                self.file_nr + 1, self.opts, self.split_identifier, header=self.lines[0])
            return buffer.process_or_write(line_nr, line)
        if cur_line_is_last:
            self.prev_line_is_last = cur_line_is_last
        self.lines.append(line)
        return self


class Splitter:

    def __init__(self, opts: SplitOptions, split_identifier: SplitIdentifier) -> None:
        self.opts = opts
        self.split_identifier = split_identifier

    def split(self, in_file: str):
        with open(in_file, 'r') as f:
            buffer = None
            for line_nr, line in enumerate(f):
                if buffer is None:  # for the first line, just consider the header
                    buffer = SplitBuffer(
                        1, self.opts, self.split_identifier, header=line)
                    continue
                buffer = buffer.process_or_write(line_nr, line)
        if buffer and len(buffer.lines) > 1:  # if there's more than just a header
            buffer.save()  # saver remaining


def split_file(in_file: str, nr_of_lines: int, out_file_format: str) -> None:
    """Splits a file into multiple files of the specified number of lines (or close to it).

    PS! This splitting is currently only designed for a narrow type of CSV files.
        This was created to split the MIMIC-III notes into parts. It may work with
        later MIMIC releases but is unlikely to work for other datasets.

    Args:
        in_file (str): _description_
        nr_of_lines (int): _description_
        out_file_format (str): _description_
    """
    opts = SplitOptions(lines_at_a_time=nr_of_lines,
                        out_file_format=out_file_format)
    split_identifier = SplitIdentifier()
    splitter = Splitter(opts, split_identifier)
    splitter.split(in_file)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Need to specify in original file name and target file format')
        sys.exit(2)
    orig_file = sys.argv[1]
    target_format = sys.argv[2]
    if '%d' not in target_format:
        print('Target format needs to contain "%d" for including number in the file names')
        sys.exit(2)
    nr_of_lines = 300000
    if len(sys.argv) > 3:
        try:
            nr_of_lines = int(sys.argv[3])
        except ValueError:
            print(
                'Third argument needs to be numeric (for the number of lines per each split)')
            sys.exit(2)
    split_file(orig_file, nr_of_lines, target_format)
