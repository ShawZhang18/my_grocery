import subprocess
import os
import signal
import sys
import os
import getopt
import string
from enum import Enum
from xml.etree import ElementTree as eTree


### 在此处添加需要跟踪的工程目录名称
project_name_list = ["googletest","projectA","projectB","projectC"]

project_dir = "../"

# path = os.getcwd()
# for i in dir_list:
#     os.chdir(path + r"\\" + i)
#     command = "git status"
#     complete_process_obj = subprocess.run(command, stdout=subprocess.PIPE)
#     print("######  current dir:" + i + '\n')
#     print(complete_process_obj.stdout.decode())

class PrintColor:
    WHITE = '\033[97m'
    # 蓝绿色
    CYAN = '\033[96m'
    # 品红
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(Enum):
    PULL = 'pull'
    PUSH = 'push'
    BRANCH = 'branch'
    CHECKOUT = 'checkout'
    STATUS = 'status'
    MERGE = 'merge'
    CUSTOM = '-c'

# 输出带有颜色的日志
def print_with_color(msg, *print_colors):
    # pc = ''.join(print_colors)
    # print('{0}{1}{2}'.format(pc, msg, PrintColor.END), flush=True)
    print(msg)

def check_none(element, err_msg):
    if element is None:
        print_with_color(err_msg, PrintColor.RED)
        sys.exit(-1)

def check_empty(value, err_msg):
    if not value.strip():
        print_with_color(err_msg, PrintColor.RED)
        sys.exit(-1)

# 中断执行
def signal_handler(signal_num, frame):
    sys.exit(signal_num)

def check_project_exist(project_dir, project_name):
    if not os.path.exists(project_dir):
        print_with_color('err: project `{0}` is not exist, you may need to sync projects'.format(project_name),
                         PrintColor.RED)
        sys.exit(-1)

# manifest 上一级目录
def get_parent_dir():
    return os.path.dirname(project_dir)

def pull(custom_dir=None, branch_name='master'):
    # 如果用户自定了目录，则使用用户自定义的目录
    target_path = get_parent_dir() if custom_dir is None else custom_dir
    for project_name in project_name_list:
        # git_url = manifest.projects[project_name]
        project_dir = os.path.join(target_path, project_name)

        # 项目文件夹不存在,使用git clone
        if not os.path.exists(project_dir):
            os.chdir(target_path)
            print_with_color('{0:-^80}'.format(project_dir), PrintColor.GREEN)
            os.system('git clone -b {0} {1} {2}'.format(branch_name, git_url, project_name))
        elif os.path.exists(os.path.join(project_dir, '.git')):
            # git pull
            # print_with_color('{0:-^50}'.format(project_name), PrintColor.GREEN)
            print("####" + project_name)
            os.chdir(project_dir)
            pull_result = os.popen('git {0}'.format(Command.PULL.value)).readlines()
            print(pull_result)
        else:
            # 文件夹存在，但是 .git 文件夹为空
            print_with_color('{0:-^50}'.format(project_name), PrintColor.GREEN)
            print_with_color('目标文件夹 {0} 已经存在，并且不为空'.format(project_name), PrintColor.RED)
            sys.exit(-1)


def push(has_option=False):
    target_path = get_parent_dir()
    for project_name in project_name_list:
        project_dir = os.path.join(target_path, project_name)
        check_project_exist(project_dir, project_name)
        print_with_color('{0:-^50}'.format(project_name), PrintColor.GREEN)
        os.chdir(project_dir)
        push_option = ''
        if has_option:
            remote = get_remote(project_dir)
            actual_branch = get_actual_branch(project_dir)
            push_option = ' -u {0} {1}'.format(remote, actual_branch)

        os.system('git {0} {1}'.format(Command.PUSH.value, push_option))


def checkout(target_branch):
    target_path = get_parent_dir()
    for project_name in project_name_list:
        project_dir = os.path.join(target_path, project_name)
        check_project_exist(project_dir, project_name)
        os.chdir(project_dir)
        os.system('git {0} {1}'.format(Command.CHECKOUT.value, target_branch))


def status():
    target_path = get_parent_dir()
    for project_name in project_name_list:
        project_dir = os.path.join(target_path, project_name)
        check_project_exist(project_dir, project_name)
        os.chdir(project_dir)
        r = os.popen('git status -s')
        lines = r.read().splitlines(False)
        if len(lines) == 0:
            r2 = os.popen('git status')
            lines2 = r2.read().splitlines(False)
            msg = None
            for line in lines2:
                if line.find('All conflicts fixed but you are still merging') != -1:
                    msg = ('Project {0} need to commit (All conflicts fixed but you are still merging)'.format(
                        project_name))
                if line.find('use "git pull"') != -1:
                    msg = ('Project {0} need to pull'.format(project_name))
                elif line.find('use "git push"') != -1:
                    msg = ('Project {0} need to push'.format(project_name))
                # other situations
            if msg is None:
                print_with_color('Project {0} is clean'.format(project_name))
            else:
                print_with_color(msg, PrintColor.YELLOW)
            continue
        else:
            print_with_color('Project {0}/'.format(project_name), PrintColor.YELLOW)
        for line in lines:
            status_file = line.rsplit(" ", 1)
            print('     {0}{1}{2} {3}'.format(PrintColor.RED, status_file[0], PrintColor.END, status_file[1]))


def branch():
    target_path = get_parent_dir()
    branch_map = {}
    all_result = []
    for project_name in project_name_list:
        project_dir = os.path.join(target_path, project_name)
        check_project_exist(project_dir, project_name)
        os.chdir(project_dir)
        r = os.popen('git branch')
        lines = r.read().splitlines(False)
        for line in lines:
            if line.startswith('*'):
                current_branch = line[2:]
                if current_branch in branch_map:
                    branch_map[current_branch] = branch_map[current_branch] + 1
                else:
                    branch_map[current_branch] = 1

                all_result.append(project_name + " : " + current_branch)

    if len(branch_map) > 0:
        if len(branch_map) == 1:
            print('all projects in branch', end=' ')
            print_with_color(next(iter(branch_map)), PrintColor.GREEN)
        else:
            print_with_color('There are {0} projects:'.format(len(project_name_list)), PrintColor.YELLOW)
            for name in branch_map:
                print_with_color('   {0} projects in {1}'.format(branch_map[name], name), PrintColor.GREEN)
        for i in all_result:
            print(i)

def execute_raw_command(raw_command):
    target_path = get_parent_dir()
    for project_name in project_name_list:
        project_dir = os.path.join(target_path, project_name)
        check_project_exist(project_dir, project_name)
        os.chdir(project_dir)
        os.system(raw_command)

def execute():
    #chd:r: 中的":"表示该短命令后面可以接参数，后面的方括号表示前面短命令对应的长命令名称， help即为h的对应长命令
    options, args = getopt.getopt(sys.argv[1:], 'chd:r:', ['help'])

    for name, value in options:
        if name == '-c':
            raw_git_command = ' '.join(args)
            execute_raw_command(raw_git_command)
            return
        # elif name in ('-h', '--help'):
        #     repos_help()
        #     return
        # elif name == '-d':
        #     delete_branch(value)
        #     return
        # elif name == '-r':
        #     delete_branch(value, True)
        else:
            print_with_color('error: unknown switch "{0}"'.format(name))
            return

    for arg in args:
        if arg == Command.PULL.value or arg == 'sync':
            # -b branch_name -d custom_dir
            command_d = '-d'
            custom_dir = None
            if command_d in args:
                d_index = args.index(command_d)
                if len(args) > d_index + 1:
                    custom_dir = args[d_index + 1]
                else:
                    print_with_color('err: command -d must set directory, like: -d "C:\\Program Files (x86)"',
                                     PrintColor.RED)
                    sys.exit(-1)

            final_branch = None
            # 判断当前文件夹是否是 git 目录，优先使用此仓库 branch
            current_dir = os.path.abspath(os.path.dirname(__file__))
            if os.path.exists(os.path.join(current_dir, '.git')):
                final_branch = get_actual_branch(current_dir)

            command_b = '-b'
            if final_branch is None:
                if command_b in args:
                    b_index = args.index(command_b)
                    if len(args) > b_index + 1:
                        final_branch = args[b_index + 1]
                    else:
                        print_with_color('err: command -b must set branch_name, like: -b master', PrintColor.RED)
                        sys.exit(-1)

            pull(custom_dir, final_branch)
            break
        elif arg == Command.PUSH.value:
            push('-u' in args)
            break
        elif arg == Command.BRANCH.value:
            branch()
            break
        elif arg == Command.STATUS.value:
            status()
            break
        elif arg == Command.CHECKOUT.value:
            if len(args) > 1:
                target_branch = args[1]
                checkout(target_branch)
            else:
                print_with_color('err: git checkout command must contain target branch', PrintColor.RED)
            break
        elif arg == Command.MERGE.value:
            if len(args) > 1:
                source_branch = args[1]
                merge(source_branch)
            else:
                print_with_color('err: git merge command must contain source branch', PrintColor.RED)
            break
        elif arg == 'cfb':
            if len(args) > 1:
                new_branch = args[1]
                execute_cfb(new_branch, '-p' in args)
            else:
                print_with_color('err: cfb command must contain new branch name', PrintColor.RED)
            break
        else:
            print_with_color("err: unsupported command '{0}', see 'python repos.py -h or --help'".format(arg),
                             PrintColor.RED)


def main():
    # Ctrl+C 会触发 SIGINT 信号
    signal.signal(signal.SIGINT, signal_handler)
    execute()

if __name__ == '__main__':
    main()