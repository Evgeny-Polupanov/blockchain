# file = open('demo.txt', mode='a')
# file.write('Hello from Python.\n')
# file.close()

with open('demo.txt', mode='r') as file:
    line = file.readline()
    while line:
        print(line)
        line = file.readline()

    # for line in file_content:
    #     print(line[:-1])
print('Done')
