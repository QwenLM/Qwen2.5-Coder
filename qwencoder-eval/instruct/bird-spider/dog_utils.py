import argparse
import enum
import json
import re
from datetime import datetime
from pathlib import Path


def norm_path(file):
    return str(Path(file).resolve())


class ProcessStatus(enum.Enum):
    TRACKED = enum.auto()
    RUNNING = enum.auto()
    FINISH = enum.auto()
    SKIPPED = enum.auto()

    def to_str(status):
        return {
            ProcessStatus.TRACKED: "tracked",
            ProcessStatus.RUNNING: "running",
            ProcessStatus.FINISH: "finish",
            ProcessStatus.SKIPPED: "skipped",
        }.get(status, "unknown")

    def to_file(status):
        status_file = {
            ProcessStatus.RUNNING: ".watchdog_running",
            ProcessStatus.FINISH: ".watchdog_finish",
            ProcessStatus.SKIPPED: ".watchdog_skipped",
        }.get(status, None)
        return status_file


class TaskStatus(enum.Enum):
    TASK_SUCCESS = enum.auto()
    TASK_FAILED = enum.auto()

    def to_str(self):
        return {
            TaskStatus.TASK_SUCCESS: "success",
            TaskStatus.TASK_FAILED: "failed",
        }.get(self, "unknown")

    def to_file(self):
        return {
            TaskStatus.TASK_SUCCESS: ".task_success",
            TaskStatus.TASK_FAILED: ".task_failed",
        }.get(self, None)


def cmd_pretty_and_save(cmd_s, save_file, task_id=None):
    if not isinstance(cmd_s, list):
        cmd_s = [cmd_s]

    with Path(save_file).open("a") as f:
        if task_id:
            f.write(f"# Task id: {task_id}\n")

        f.write(f"# Start at: {datetime.now().strftime('%m/%d %H:%M:%S')}\n\n")

        for cmd in cmd_s:
            pretty_cmd = cmd.replace(";", "\n\n").replace(" --", " \\\n\t--")
            f.write(f"{pretty_cmd}\n\n")

    return pretty_cmd


class SubFolderState:

    def __init__(self, sub2status=None, sub2kwargs=None, reverse=True, do_sort=True):
        if not sub2status:
            self.sub = {}  # {subfolder_stem: ProcessStatus}
        else:
            self.sub = sub2status

        if not sub2kwargs:
            self.sub2kwargs = {}
        else:
            self.sub2kwargs = sub2kwargs

        self.reverse = reverse
        self.do_sort = do_sort
        self._timestamp = datetime.now()

    def __eq__(self, new_fs):
        for fs in new_fs:
            if fs not in self.sub:
                return False
        return True

    def __len__(self):
        return len(self.sub)

    def maybe_sort(self, data):
        if self.do_sort:
            return sorted(data, key=natural_keys, reverse=self.reverse)
        else:
            return data

    def get_list_by_status(self, status=None):
        if status:
            filtered = [e[0] for e in self.sub.items() if e[1] == status]
        else:
            filtered = list(self.sub.keys())

        return self.maybe_sort(filtered)

    def __repr__(self):
        s = f"<SubFolderState> {len(self.sub)} folders [{self._timestamp.strftime('%m/%d %H:%M:%S')}] \n"

        status_to_list = {
            "tracked": self.get_list_by_status(ProcessStatus.TRACKED),
            "running": self.get_list_by_status(ProcessStatus.RUNNING),
            "finish": self.get_list_by_status(ProcessStatus.FINISH),
            "skipped": self.get_list_by_status(ProcessStatus.SKIPPED),
        }

        for key in ["tracked", "running", "skipped", "finish"]:
            subfolder_list = status_to_list[key]
            s += f"\tStatus={key:<10} | Len={len(subfolder_list)}\n"
            if key == "finish":
                continue
            for idx, folder in enumerate(subfolder_list):
                is_last = idx == len(subfolder_list) - 1
                prefix = "\t\t" + ("└──" if is_last else "├──")
                s += f"{prefix}{folder}\n"

        return s

    def has_unfinished_tracked(self):
        tracked_list = [e[0] for e in self.sub.items() if e[1] == ProcessStatus.TRACKED]
        return len(tracked_list)

    def has_unfinished_skipped(self):
        skipped_list = [e[0] for e in self.sub.items() if e[1] == ProcessStatus.SKIPPED]
        return len(skipped_list)

    def get_first_marked(self, mark=ProcessStatus.TRACKED):
        tracked_list = [e[0] for e in self.sub.items() if e[1] == mark]
        if not len(tracked_list):
            return None
        return self.maybe_sort(tracked_list)[0]

    def get_first_tracked(self):
        return self.get_first_marked(ProcessStatus.TRACKED)

    def get_first_tracked_kwargs(self, signature):
        return self.sub2kwargs[signature]

    def get_first_skipped(self):
        return self.get_first_marked(ProcessStatus.SKIPPED)

    def set_process_status(self, output_folder, subfolder, status):
        status_file = ProcessStatus.to_file(status)
        status_file_path = Path(output_folder).joinpath(subfolder).joinpath(status_file)

        if status_file_path.exists():
            return False
        else:
            with status_file_path.open("w") as f:
                f.write(status_file)
            print(f"Locker set => {status_file_path}")
            return True

    def del_process_status(self, output_folder, subfolder, status):
        status_file = ProcessStatus.to_file(status)
        status_file_path = Path(output_folder).joinpath(subfolder).joinpath(status_file)

        if not status_file_path.exists():
            return False
        status_file_path.unlink()
        print(f"Locker removed => {status_file_path}")
        return True


def natural_keys(text):

    def atoi(t):
        return int(t) if t.isdigit() else t

    return [atoi(c) for c in re.split(r"(\d+)", text)]


def split_comma(str_patterns):
    patterns = [e.strip() for e in str_patterns.split(",")]
    patterns = [e for e in patterns if e]
    return patterns


def subfolder_collect(folder, watch_output_root, depth, include, exclude, target_pattern=".saved"):
    include_patterns, exclude_patterns = split_comma(include), split_comma(exclude)

    def test_collectable(subfolder):
        if not Path(subfolder).is_dir():
            return False
        return Path(subfolder).joinpath(target_pattern).exists()

    if depth > 0:
        saved_pattern = ""
        patterns = []
        for d in range(depth):
            saved_pattern += "*/"
            patterns.append(saved_pattern)
        patterns = [e + target_pattern for e in patterns]
    elif depth < 0:
        patterns = [f"**/*/{target_pattern}"]
    else:  # depth = 0, evaluate the current folder
        patterns = [target_pattern]

    subfolders = {}
    for pat in patterns:
        for f in folder.glob(pat):
            maybe_folder = f.parent
            if test_collectable(maybe_folder):
                if any([pat in str(maybe_folder) for pat in exclude_patterns]):  # all must not appear
                    continue
                if not all([pat in str(maybe_folder) for pat in include_patterns]):  # must appear at least one
                    continue

                relative_to_root = str(maybe_folder.relative_to(folder))
                watchdog_output = watch_output_root.joinpath(relative_to_root)

                status = ProcessStatus.TRACKED
                for to_test_status in [ProcessStatus.RUNNING, ProcessStatus.FINISH, ProcessStatus.SKIPPED]:
                    maybe_status_file = ProcessStatus.to_file(to_test_status)
                    if watchdog_output.joinpath(maybe_status_file).exists():
                        status = to_test_status
                        break

                subfolders[relative_to_root] = status
    return SubFolderState(subfolders)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--in_f", type=str)
    parser.add_argument("--out_f", type=str)
    parser.add_argument("--fix", default=False, action="store_true")

    args = parser.parse_args()

    in_f = Path(args.in_f)
    out_f = Path(args.out_f)

    if not in_f.exists():
        raise ValueError(f"Input file does not exist: {in_f}")
    if out_f.exists():
        print(f"[WARNING] Output file already exist, overwrite will happen: {out_f}")

    with in_f.open("r") as f:
        d = json.load(f)
    lines = [e[0] for e in d]

    with out_f.open("w") as f:
        for line in lines:
            if args.fix:
                line = line.strip().replace("\r", "\t").replace("\n", "\t")
            f.write(f"{line}\n")

    print(f"Saved at {out_f}")
