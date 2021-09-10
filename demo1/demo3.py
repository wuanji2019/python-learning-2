import time


def decorator(func):
    def punch(*args, **kwargs):
        print(time.strftime('%Y-%m-%d', time.localtime(time.time())))
        func(*args, **kwargs)

    return punch


@decorator
def punch(name, department):
    print('昵称：{0}  部门：{1} 上班打卡成功'.format(name, department))


@decorator
def print_args(reason, **kwargs):
    print(reason)
    print(kwargs)


punch('两点水', '做鸭事业部')
print_args('两点水', sex='男', age=99)