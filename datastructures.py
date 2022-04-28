def unlimited_arguments(*args, **kwargs):
    for argument in args:
        print(argument)
    for kwarg in kwargs:
        print(kwargs[kwarg])


unlimited_arguments(1, 2, 3, 4, name='Max', age=29)
