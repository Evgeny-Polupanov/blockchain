with open('demo.txt', mode='r') as file:
    line = file.readline()
    while line:
        print(line)
        line = file.readline()

print('Done')
